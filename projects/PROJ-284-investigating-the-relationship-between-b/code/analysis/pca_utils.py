"""PCA utilities for task T023a.

This module implements the core PCA workflow required by T023a:
loading aggregated metrics, fitting PCA with exactly 2 components,
computing loadings and factor scores, and writing them to CSV.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

from code.logging_config import get_logger

logger = get_logger(__name__)

# -----------------------------------------------------------------------
# Core PCA functions
# -----------------------------------------------------------------------

def load_metrics_data(csv_path: Path) -> pd.DataFrame:
    """Load the aggregated metrics CSV.

    Parameters
    ----------
    csv_path: Path
        Path to ``data/analysis/aggregated_metrics.csv`` produced by T022.

    Returns
    -------
    pd.DataFrame
        DataFrame containing the metrics. The column ``subject_id`` is
        expected to be present; if it is missing the function will still
        return the DataFrame unchanged.
    """
    if not csv_path.is_file():
        raise FileNotFoundError(f"Metrics file not found: {csv_path}")
    logger.log("load_metrics_data", path=str(csv_path))
    df = pd.read_csv(csv_path)
    logger.log("metrics_loaded", rows=len(df), columns=list(df.columns))
    return df

def run_pca_on_metrics(
    df: pd.DataFrame, n_components: int = 2
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Fit PCA on the metric columns and return loadings and scores.

    The function expects a column named ``subject_id`` that will be kept
    alongside the factor scores. All other columns are treated as features
    for the PCA.

    Parameters
    ----------
    df: pd.DataFrame
        DataFrame returned by :func:`load_metrics_data`.
    n_components: int
        Number of principal components to retain (must be 2 for this task).

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame]
        * **loadings** – DataFrame of shape (n_features, n_components)
          with the PCA component loadings. Index are the original metric
          names; columns are ``PC1``, ``PC2``.
        * **scores** – DataFrame of shape (n_subjects, n_components + 1)
          containing ``subject_id`` and the factor scores named
          ``pca_factor_1`` and ``pca_factor_2``.
    """
    if n_components != 2:
        raise ValueError(f"n_components must be 2, got {n_components}")

    logger.log("pca_start", n_components=n_components)

    # Separate subject_id from metric columns
    if "subject_id" not in df.columns:
        raise KeyError("DataFrame must contain 'subject_id' column")

    subject_ids = df["subject_id"].values
    metric_cols = [c for c in df.columns if c != "subject_id"]

    if len(metric_cols) == 0:
        raise ValueError("No metric columns found (only subject_id)")

    X = df[metric_cols].values

    # Fit PCA with exactly 2 components
    pca = PCA(n_components=2)
    scores_array = pca.fit_transform(X)

    # Log variance explained
    var_explained = pca.explained_variance_ratio_
    cumsum_var = np.cumsum(var_explained)
    logger.log(
        "pca_variance_explained",
        pc1=float(var_explained[0]),
        pc2=float(var_explained[1]),
        cumulative=float(cumsum_var[-1]),
    )

    # Build loadings DataFrame
    loadings_df = pd.DataFrame(
        pca.components_.T,
        index=metric_cols,
        columns=["PC1", "PC2"],
    )

    # Build scores DataFrame with subject_id and factor scores
    scores_df = pd.DataFrame(
        {
            "subject_id": subject_ids,
            "pca_factor_1": scores_array[:, 0],
            "pca_factor_2": scores_array[:, 1],
        }
    )

    logger.log(
        "pca_complete",
        n_subjects=len(scores_df),
        n_features=len(metric_cols),
    )

    return loadings_df, scores_df

def save_pca_outputs(
    loadings: pd.DataFrame,
    scores: pd.DataFrame,
    loadings_path: Path,
    scores_path: Path,
) -> None:
    """Write PCA results to CSV files.

    Parameters
    ----------
    loadings: pd.DataFrame
        Loadings DataFrame returned by :func:`run_pca_on_metrics`.
    scores: pd.DataFrame
        Scores DataFrame returned by :func:`run_pca_on_metrics`.
    loadings_path: Path
        Destination path for the loadings CSV (``pca_loadings.csv``).
    scores_path: Path
        Destination path for the factor scores CSV (``factor_scores.csv``).
    """
    # Ensure parent directories exist
    loadings_path.parent.mkdir(parents=True, exist_ok=True)
    scores_path.parent.mkdir(parents=True, exist_ok=True)

    # Write loadings
    loadings.to_csv(loadings_path)
    logger.log("pca_loadings_written", path=str(loadings_path))

    # Write scores
    scores.to_csv(scores_path, index=False)
    logger.log("pca_scores_written", path=str(scores_path), rows=len(scores))

def run_pca_pipeline(analysis_dir: Path = Path("data/analysis")) -> None:
    """High‑level entry point used by ``code/analysis/correlations.py``.

    This function orchestrates the full PCA workflow required by task T023a.
    It is also safe to call directly (e.g. ``python -m code.analysis.pca_utils``)
    for debugging or ad‑hoc runs.

    Parameters
    ----------
    analysis_dir: Path
        Directory containing ``aggregated_metrics.csv`` and where the
        PCA outputs will be written (default: ``data/analysis``).
    """
    logger.log("run_pca_pipeline_start", analysis_dir=str(analysis_dir))

    # Load aggregated metrics
    metrics_path = analysis_dir / "aggregated_metrics.csv"
    df = load_metrics_data(metrics_path)

    # Run PCA with exactly 2 components
    loadings, scores = run_pca_on_metrics(df, n_components=2)

    # Verify that exactly 2 components were produced
    assert loadings.shape[1] == 2, f"Expected 2 components, got {loadings.shape[1]}"
    assert "pca_factor_1" in scores.columns, "Missing pca_factor_1 column"
    assert "pca_factor_2" in scores.columns, "Missing pca_factor_2 column"

    # Write outputs
    loadings_path = analysis_dir / "pca_loadings.csv"
    scores_path = analysis_dir / "factor_scores.csv"
    save_pca_outputs(loadings, scores, loadings_path, scores_path)

    logger.log("run_pca_pipeline_complete")

# -----------------------------------------------------------------------
# CLI entry point
# -----------------------------------------------------------------------

if __name__ == "__main__":
    run_pca_pipeline()
