import os
import time
import datetime
import math
import random
import pandas as pd
from dotenv import load_dotenv
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from requests.exceptions import HTTPError, RequestException

# ---------------- Config ----------------
MAX_REPOS = 200           # total de repositórios a coletar (reduza p/ teste, ex: 10)
REPOS_PAGE_SIZE = 20      # tamanho da página para busca de repositórios
PRS_PAGE_SIZE = 25        # PRs por página por repositório
MAX_RETRIES = 8
RETRY_BASE = 2.0          # base do backoff exponencial
RETRY_CAP = 60.0          # limite máximo de espera
PAGE_THROTTLE_S = 2.0     # intervalo entre páginas (repos/PRs)
TRANSPORT_TIMEOUT = 30    # timeout de request (segundos)

# --------------- Autenticação ---------------
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise SystemExit("Erro: GITHUB_TOKEN não encontrado no .env")

headers = {
    "Authorization": f"bearer {GITHUB_TOKEN}",
    "User-Agent": "data-collector/1.0 (+https://github.com/)",  # bom ter
}

transport = RequestsHTTPTransport(
    url="https://api.github.com/graphql",
    headers=headers,
    use_json=True,
    timeout=TRANSPORT_TIMEOUT,
)

client = Client(transport=transport, fetch_schema_from_transport=False)

# --------- Queries ----------
Q_SEARCH_REPOS = gql("""
query ($cursor: String, $pageSize: Int!) {
  search(query: "stars:>1000 sort:stars-desc", type: REPOSITORY, first: $pageSize, after: $cursor) {
    edges {
      node {
        ... on Repository {
          name
          url
          createdAt
          pushedAt
          isFork
          isArchived
          stargazerCount
          owner { login }
          releases { totalCount }
          defaultBranchRef { name }
          pullRequests(states: [MERGED, CLOSED]) { totalCount }
        }
      }
    }
    pageInfo { hasNextPage endCursor }
  }
}
""")

Q_REPO_PRS = gql("""
query ($owner: String!, $name: String!, $cursor: String, $pageSize: Int!) {
  repository(owner: $owner, name: $name) {
    pullRequests(
      states: [MERGED, CLOSED]
      orderBy: {field: CREATED_AT, direction: DESC}
      first: $pageSize
      after: $cursor
    ) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes {
        number
        title
        url
        state
        createdAt
        closedAt
        mergedAt
        author { login }
        reviews { totalCount }
      }
    }
  }
}
""")

# --------------- Utilidades ---------------
def backoff_sleep(attempt: int):
    wait = min(RETRY_CAP, (RETRY_BASE ** attempt)) * (1 + 0.2 * random.random())
    time.sleep(wait)

def execute_with_retries(query, variables):
    attempt = 0
    while True:
        try:
            return client.execute(query, variable_values=variables)
        except (HTTPError, RequestException, Exception) as e:
            attempt += 1
            if attempt > MAX_RETRIES:
                raise
            print(f"Erro (tentativa {attempt}/{MAX_RETRIES}): {e}. Aguarde…")
            backoff_sleep(attempt)

def filter_pull_requests(prs):
    """Filtra PRs com pelo menos 1 review e tempo > 1h"""
    filtered = []
    for pr in prs:
        if pr["reviews"]["totalCount"] < 1:
            continue
        created = datetime.datetime.fromisoformat(pr["createdAt"].replace("Z", "+00:00"))
        closed_str = pr.get("closedAt") or pr.get("mergedAt")
        if not closed_str:
            continue
        closed = datetime.datetime.fromisoformat(closed_str.replace("Z", "+00:00"))
        if (closed - created).total_seconds() <= 3600:
            continue
        filtered.append(pr)
    return filtered

# --------------- Coleta ---------------
def collect_repos():
    all_edges = []
    cursor = None
    while len(all_edges) < MAX_REPOS:
        data = execute_with_retries(Q_SEARCH_REPOS, {"cursor": cursor, "pageSize": REPOS_PAGE_SIZE})
        search = data["search"]
        edges = search.get("edges", [])
        all_edges.extend(edges)
        page_info = search.get("pageInfo") or {}
        cursor = page_info.get("endCursor")
        print(f"Coletados {len(all_edges)} repositórios…")
        if not page_info.get("hasNextPage") or len(all_edges) >= MAX_REPOS:
            break
        time.sleep(PAGE_THROTTLE_S)
    return all_edges[:MAX_REPOS]

def collect_repo_prs(owner: str, name: str, total_prs: int):
    """Pagina PRs por repositório em lotes menores"""
    cursor = None
    collected = []
    pages = 0
    while True:
        data = execute_with_retries(Q_REPO_PRS, {"owner": owner, "name": name, "cursor": cursor, "pageSize": PRS_PAGE_SIZE})
        prs = data["repository"]["pullRequests"]
        nodes = prs.get("nodes", []) or []
        filtered = filter_pull_requests(nodes)
        collected.extend(filtered)

        pages += 1
        print(f"  {owner}/{name}: página {pages}, PRs válidos até agora {len(collected)}")

        if not prs["pageInfo"]["hasNextPage"]:
            break
        cursor = prs["pageInfo"]["endCursor"]
        time.sleep(PAGE_THROTTLE_S)
        if pages >= 50:
            break
    return collected

def run():
    repos = collect_repos()
    rows = []
    for i, edge in enumerate(repos, start=1):
        repo = edge["node"]
        if repo["pullRequests"]["totalCount"] < 100:
            continue
        owner = repo["owner"]["login"]
        name = repo["name"]

        print(f"[{i}/{len(repos)}] Processando repositório {owner}/{name}…")
        valid_prs = collect_repo_prs(owner, name, repo["pullRequests"]["totalCount"])
        if not valid_prs:
            print(f"  Nenhum PR válido em {owner}/{name}")
            continue

        for pr in valid_prs:
            rows.append({
                "repo_name": name,
                "repo_owner": owner,
                "repo_url": repo["url"],
                "repo_stars": repo["stargazerCount"],
                "repo_createdAt": repo["createdAt"],
                "repo_pushedAt": repo["pushedAt"],
                "repo_isFork": repo.get("isFork", False),
                "repo_isArchived": repo.get("isArchived", False),
                "repo_releases": (repo.get("releases") or {}).get("totalCount", 0),
                "repo_defaultBranch": (repo.get("defaultBranchRef") or {}).get("name"),

                "pr_number": pr["number"],
                "pr_title": pr["title"],
                "pr_url": pr["url"],
                "pr_author": (pr.get("author") or {}).get("login"),
                "pr_state": pr["state"],
                "pr_createdAt": pr["createdAt"],
                "pr_closedAt": pr.get("closedAt"),
                "pr_mergedAt": pr.get("mergedAt"),
                "pr_reviews": pr["reviews"]["totalCount"],
            })

    df = pd.DataFrame(rows)
    df.to_csv("pull_requests.csv", index=False, encoding="utf-8")
    print(f"\n✅ Arquivo pull_requests.csv salvo com {len(rows)} PRs válidos.")

if __name__ == "__main__":
    run()
