# graphics.py
# -*- coding: utf-8 -*-
"""
Gera tabelas (medianas e correlações) e gráficos para RQ01–RQ08 a partir de pull_requests.csv.

Uso:
  python graphics.py --csv pull_requests.csv --out lab03_outputs
"""

import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # salva PNG sem abrir janela
import matplotlib.pyplot as plt

_HAVE_SCIPY = True
try:
    from scipy.stats import spearmanr, pearsonr
except Exception:
    _HAVE_SCIPY = False

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="caminho para pull_requests.csv")
    ap.add_argument("--out", default="lab03_outputs", help="pasta de saída")
    ap.add_argument("--method", choices=["spearman", "pearson"], default="spearman",
                    help="método de correlação")
    return ap.parse_args()

def corr_with_test(x, y, method="spearman"):
    """Retorna (rho, p, n). Se SciPy não estiver disponível, p=np.nan."""
    tmp = pd.DataFrame({"x": x, "y": y}).dropna()
    n = len(tmp)
    if n < 3:
        return (np.nan, np.nan, n)
    if method == "pearson":
        if _HAVE_SCIPY:
            r, p = pearsonr(tmp["x"], tmp["y"])
        else:
            r = tmp["x"].corr(tmp["y"], method="pearson")
            p = np.nan
        return (r, p, n)
    # spearman
    if _HAVE_SCIPY:
        r, p = spearmanr(tmp["x"], tmp["y"])
    else:
        r = tmp["x"].corr(tmp["y"], method="spearman")
        p = np.nan
    return (r, p, n)

def main():
    args = parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.csv)

    # ---- Pré-processamento ----
    created = pd.to_datetime(df.get("pr_createdAt"), errors="coerce", utc=True)
    closed_or_merged = pd.to_datetime(df.get("pr_closedAt"), errors="coerce", utc=True)
    merged_at = pd.to_datetime(df.get("pr_mergedAt"), errors="coerce", utc=True)
    finished = closed_or_merged.fillna(merged_at)

    df["analysis_time_hours"] = (finished - created).dt.total_seconds() / 3600.0

    pr_state = df.get("pr_state").astype(str).str.upper()
    df["status_numeric"] = (pr_state == "MERGED").astype(float)

    # métricas de tamanho
    df["pr_additions"] = pd.to_numeric(df.get("pr_additions"), errors="coerce")
    df["pr_deletions"] = pd.to_numeric(df.get("pr_deletions"), errors="coerce")
    df["pr_changed_files"] = pd.to_numeric(df.get("pr_changed_files"), errors="coerce")
    df["total_changes"] = df["pr_additions"].fillna(0) + df["pr_deletions"].fillna(0)

    # descrição
    if "pr_description_len" not in df.columns:
        if "pr_body" in df.columns:
            df["pr_description_len"] = df["pr_body"].fillna("").astype(str).str.len()
        else:
            df["pr_description_len"] = np.nan
    else:
        df["pr_description_len"] = pd.to_numeric(df["pr_description_len"], errors="coerce")

    # interações e revisões
    df["pr_comments"] = pd.to_numeric(df.get("pr_comments"), errors="coerce")
    df["pr_participants"] = pd.to_numeric(df.get("pr_participants"), errors="coerce")
    df["pr_reviews"] = pd.to_numeric(df.get("pr_reviews"), errors="coerce")

    # ---- Tabelas de medianas ----
    num_cols = [
        "pr_changed_files","pr_additions","pr_deletions","total_changes",
        "analysis_time_hours","pr_description_len","pr_comments",
        "pr_participants","pr_reviews","status_numeric"
    ]
    for c in num_cols:
        if c not in df.columns:
            df[c] = np.nan
        df[c] = pd.to_numeric(df[c], errors="coerce")

    overall_medians = df[num_cols].median(numeric_only=True).rename("median_all")
    overall_medians.to_csv(out_dir / "overall_medians.csv")

    if "pr_state" in df.columns:
        by_status_medians = df.groupby(pr_state)[
            ["pr_changed_files","pr_additions","pr_deletions","total_changes",
             "analysis_time_hours","pr_description_len","pr_comments",
             "pr_participants","pr_reviews"]
        ].median(numeric_only=True)
        by_status_medians.to_csv(out_dir / "by_status_medians.csv")

    non_null_counts = df[num_cols].notna().sum().rename("non_null_count")
    non_null_counts.to_csv(out_dir / "non_null_counts.csv")

    # ---- Correlações ----
    status_y = df["status_numeric"]
    reviews_y = df["pr_reviews"]

    metrics = {
        "size": ["pr_changed_files","pr_additions","pr_deletions","total_changes"],
        "time": ["analysis_time_hours"],
        "description": ["pr_description_len"],
        "interactions": ["pr_comments","pr_participants"],
    }

    corr_status_rows = []
    for cat, cols in metrics.items():
        for m in cols:
            rho, p, n = corr_with_test(df[m], status_y, args.method)
            corr_status_rows.append({"RQ": f"A/{cat}", "metric": m, "rho": rho, "p_value": p, "n": n})
    pd.DataFrame(corr_status_rows).sort_values(["RQ","metric"]).to_csv(out_dir / "corr_with_status.csv", index=False)

    corr_reviews_rows = []
    for cat, cols in metrics.items():
        for m in cols:
            rho, p, n = corr_with_test(df[m], reviews_y, args.method)
            corr_reviews_rows.append({"RQ": f"B/{cat}", "metric": m, "rho": rho, "p_value": p, "n": n})
    pd.DataFrame(corr_reviews_rows).sort_values(["RQ","metric"]).to_csv(out_dir / "corr_with_reviews.csv", index=False)

    # ---- Gráficos ----
    def boxplot_by_status(metric, title, fname):
        data = df[[metric, "status_numeric"]].dropna()
        if data.empty:
            return
        state_txt = pr_state.loc[data.index]
        merged_vals = data.loc[state_txt == "MERGED", metric]
        closed_vals = data.loc[state_txt == "CLOSED", metric]
        plt.figure()
        plt.boxplot([merged_vals.values, closed_vals.values], labels=["MERGED","CLOSED"], showfliers=False)
        plt.title(title)
        plt.ylabel(metric)
        plt.tight_layout()
        plt.savefig(out_dir / fname, dpi=150)
        plt.close()

    def scatter_vs_reviews(metric, title, fname):
        data = df[[metric, "pr_reviews"]].dropna()
        if data.empty:
            return
        plt.figure()
        plt.scatter(data[metric].values, data["pr_reviews"].values, s=10, alpha=0.6)
        plt.xlabel(metric)
        plt.ylabel("pr_reviews")
        plt.title(title)
        plt.tight_layout()
        plt.savefig(out_dir / fname, dpi=150)
        plt.close()

    # A. Feedback final (Status)
    r, p, _ = corr_with_test(df["total_changes"], status_y, args.method)
    boxplot_by_status("total_changes",
                      f"RQ01: Tamanho (total_changes) vs Status – {args.method.title()} rho={r:.3f}, p={p if not np.isnan(p) else 'NA'}",
                      "RQ01_size_vs_status.png")

    r, p, _ = corr_with_test(df["analysis_time_hours"], status_y, args.method)
    boxplot_by_status("analysis_time_hours",
                      f"RQ02: Tempo de análise (h) vs Status – {args.method.title()} rho={r:.3f}, p={p if not np.isnan(p) else 'NA'}",
                      "RQ02_time_vs_status.png")

    r, p, _ = corr_with_test(df["pr_description_len"], status_y, args.method)
    boxplot_by_status("pr_description_len",
                      f"RQ03: Descrição (len) vs Status – {args.method.title()} rho={r:.3f}, p={p if not np.isnan(p) else 'NA'}",
                      "RQ03_desc_vs_status.png")

    r, p, _ = corr_with_test(df["pr_comments"], status_y, args.method)
    boxplot_by_status("pr_comments",
                      f"RQ04: Interações (comentários) vs Status – {args.method.title()} rho={r:.3f}, p={p if not np.isnan(p) else 'NA'}",
                      "RQ04_interactions_vs_status.png")

    # B. Nº de revisões
    r, p, _ = corr_with_test(df["total_changes"], reviews_y, args.method)
    scatter_vs_reviews("total_changes",
                       f"RQ05: Tamanho (total_changes) vs Nº de revisões – {args.method.title()} rho={r:.3f}, p={p if not np.isnan(p) else 'NA'}",
                       "RQ05_size_vs_reviews.png")

    r, p, _ = corr_with_test(df["analysis_time_hours"], reviews_y, args.method)
    scatter_vs_reviews("analysis_time_hours",
                       f"RQ06: Tempo de análise (h) vs Nº de revisões – {args.method.title()} rho={r:.3f}, p={p if not np.isnan(p) else 'NA'}",
                       "RQ06_time_vs_reviews.png")

    r, p, _ = corr_with_test(df["pr_description_len"], reviews_y, args.method)
    scatter_vs_reviews("pr_description_len",
                       f"RQ07: Descrição (len) vs Nº de revisões – {args.method.title()} rho={r:.3f}, p={p if not np.isnan(p) else 'NA'}",
                       "RQ07_desc_vs_reviews.png")

    r, p, _ = corr_with_test(df["pr_comments"], reviews_y, args.method)
    scatter_vs_reviews("pr_comments",
                       f"RQ08: Interações (comentários) vs Nº de revisões – {args.method.title()} rho={r:.3f}, p={p if not np.isnan(p) else 'NA'}",
                       "RQ08_interactions_vs_reviews.png")

    print(f"OK! Saídas em: {out_dir.resolve()}")

if __name__ == "__main__":
    main()
