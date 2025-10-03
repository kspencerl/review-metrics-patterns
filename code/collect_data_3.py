import os
import time
import datetime
import random
import pandas as pd
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from requests.exceptions import HTTPError, RequestException

# ---------------- Config ----------------
MAX_REPOS = 200           # total de repositórios a coletar
REPOS_PAGE_SIZE = 20      # tamanho da página para busca de repositórios
PRS_PAGE_SIZE = 100       # PRs por página (máximo permitido pelo GitHub GraphQL)
MAX_RETRIES = 8
RETRY_BASE = 2.0
RETRY_CAP = 60.0
PAGE_THROTTLE_S = 0.3     # menor intervalo entre páginas
TRANSPORT_TIMEOUT = 30
OUTPUT_FILE = "pull_requests_2.csv"
MAX_WORKERS = 8           # paralelismo (ajuste conforme sua máquina e limite da API)

# --------------- Autenticação ---------------
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise SystemExit("Erro: GITHUB_TOKEN não encontrado no .env")

headers = {
    "Authorization": f"bearer {GITHUB_TOKEN}",
    "User-Agent": "data-collector/2.0 (+https://github.com/)",
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
        bodyText
        reviews { totalCount }
        participants { totalCount }
        comments { totalCount }
        additions
        deletions
        changedFiles
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
            local_transport = RequestsHTTPTransport(
                url="https://api.github.com/graphql",
                headers=headers,
                use_json=True,
                timeout=TRANSPORT_TIMEOUT,
            )
            local_client = Client(transport=local_transport, fetch_schema_from_transport=False)
            return local_client.execute(query, variable_values=variables)
        except (HTTPError, RequestException, Exception) as e:
            attempt += 1
            if attempt > MAX_RETRIES:
                raise
            print(f"Erro (tentativa {attempt}/{MAX_RETRIES}): {e}. Retentando…")
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
    cursor = None
    collected = []
    while True:
        data = execute_with_retries(Q_REPO_PRS, {"owner": owner, "name": name, "cursor": cursor, "pageSize": PRS_PAGE_SIZE})
        prs = data["repository"]["pullRequests"]
        nodes = prs.get("nodes", []) or []
        filtered = filter_pull_requests(nodes)
        collected.extend(filtered)

        if not prs["pageInfo"]["hasNextPage"]:
            break
        cursor = prs["pageInfo"]["endCursor"]
        time.sleep(PAGE_THROTTLE_S)
    return collected

def process_repository(edge):
    repo = edge["node"]
    if repo["pullRequests"]["totalCount"] < 100:
        return []

    owner = repo["owner"]["login"]
    name = repo["name"]
    print(f"Processando repositório {owner}/{name}…")

    valid_prs = collect_repo_prs(owner, name, repo["pullRequests"]["totalCount"])
    rows = []
    for pr in valid_prs:
        rows.append({
            "repo_name": name,
            "repo_owner": owner,
            "repo_url": repo["url"],
            "repo_stars": repo["stargazerCount"],

            "pr_number": pr["number"],
            "pr_title": pr["title"],
            "pr_url": pr["url"],
            "pr_author": (pr.get("author") or {}).get("login"),
            "pr_state": pr["state"],
            "pr_createdAt": pr["createdAt"],
            "pr_closedAt": pr.get("closedAt"),
            "pr_mergedAt": pr.get("mergedAt"),
            "pr_reviews": pr["reviews"]["totalCount"],

            "pr_description_len": len(pr.get("bodyText") or ""),
            "pr_participants": pr["participants"]["totalCount"],
            "pr_comments": pr["comments"]["totalCount"],
            "pr_additions": pr["additions"],
            "pr_deletions": pr["deletions"],
            "pr_changed_files": pr["changedFiles"],
        })
    return rows

def run():
    repos = collect_repos()
    all_rows = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_repository, edge): edge for edge in repos}
        for future in as_completed(futures):
            try:
                rows = future.result()
                if rows:
                    df = pd.DataFrame(rows)
                    df.to_csv(OUTPUT_FILE, mode="a", header=not os.path.exists(OUTPUT_FILE), index=False, encoding="utf-8")
                    all_rows.extend(rows)
                    print(f"✔ {len(rows)} PRs salvos ({len(all_rows)} acumulados)")
            except Exception as e:
                repo = futures[future]["node"]
                print(f"⚠ Erro no repo {repo['owner']['login']}/{repo['name']}: {e}")

    print(f"\n✅ Coleta finalizada: {len(all_rows)} PRs válidos salvos em {OUTPUT_FILE}")

if __name__ == "__main__":
    run()
