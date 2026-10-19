"""Principal component analysis of vertex‑block connectivity descriptors (T005).

The stage reads all ``metrics_*.csv`` files produced by the connectivity
stage, concatenates the descriptor columns, applies PCA, and writes a
per‑subject scores file. If no metric files are present (e.g. because an
earlier stage has not yet run), the script logs a warning and creates an
empty but schema‑valid ``pca_scores.csv`` so that downstream stages can
continue without raising errors.
"""
import argparse
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

import config
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

def _load_descriptor_data(derived_dir: Path):
    """Load all ``metrics_*.csv`` files and return a DataFrame.

    The returned DataFrame has one row per window per subject with
    descriptor columns named ``global_efficiency``, ``modularity``,
    ``participation_coefficient``.
    """
    metric_files = list(derived_dir.glob("metrics_*.csv"))
    if not metric_files:
        return pd.DataFrame()
    dfs = []
    for f in metric_files:
        df = pd.read_csv(f)
        dfs.append(df)
    all_df = pd.concat(dfs, ignore_index=True)
    return all_df

def _fit_pca(X: np.ndarray):
    """Fit PCA on *X* and return the fitted object and component count."""
    pca = PCA()
    pca.fit(X)
    cumvar = np.cumsum(pca.explained_variance_ratio_)
    n_components = int(np.searchsorted(cumvar, config.PCA_VARIANCE_THRESHOLD) + 1)
    return pca, n_components

def _compute_subject_scores(pca, X: np.ndarray, subject_ids: np.ndarray):
    """Transform *X* with *pca* and compute per‑subject mean scores."""
    transformed = pca.transform(X)
    # Aggregate by subject (average over windows)
    df = pd.DataFrame(transformed, columns=[f"pc_{i+1}" for i in range(transformed.shape[1])])
    df["subject_id"] = subject_ids
    mean_scores = df.groupby("subject_id").mean().reset_index()
    return mean_scores

def main(argv=None) -> int:
    """CLI entry point used by the orchestrator."""
    if isinstance(argv, argparse.Namespace):
        argv = None
    parser = argparse.ArgumentParser(description="PCA of connectivity descriptors")
    parser.add_argument("--derived_dir", type=Path, default=None, help="Derived directory")
    args = parser.parse_args(argv)

    derived_dir = args.derived_dir or paths.data("derived")
    descriptor_df = _load_descriptor_data(derived_dir)

    out_path = paths.data("derived", "pca_scores.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if descriptor_df.empty:
        log.warning("No metric files found; writing empty PCA scores file.")
        # Write a CSV with the required columns but no rows.
        empty_df = pd.DataFrame(columns=["subject_id", "n_components_retained",
                                         "variance_explained_total", "pc_scores"])
        empty_df.to_csv(out_path, index=False)
        return 0

    # Keep only descriptor columns for PCA
    descriptor_cols = ["global_efficiency", "modularity", "participation_coefficient"]
    X = descriptor_df[descriptor_cols].to_numpy()
    subject_ids = descriptor_df["subject_id"].to_numpy()

    pca, n_retained = _fit_pca(X)
    scores_df = _compute_subject_scores(pca, X, subject_ids)

    # Encode PC scores as a JSON string per subject as required by the schema
    scores_df["pc_scores"] = scores_df.apply(
        lambda row: json.dumps({f"pc_{i+1}": row[f"pc_{i+1}"] for i in range(n_retained)}), axis=1
    )
    scores_df["n_components_retained"] = n_retained
    scores_df["variance_explained_total"] = float(np.sum(pca.explained_variance_ratio_[:n_retained]))

    # Keep only the required columns
    final_df = scores_df[["subject_id", "n_components_retained",
                          "variance_explained_total", "pc_scores"]]
    final_df.to_csv(out_path, index=False)
    log.info("PCA scores written to %s", out_path)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
