"""Utility functions for performing PCA on aggregated network metrics.

This module provides the core functionality required by task T023a:
- Loading the aggregated metrics CSV.
- Running PCA with exactly two components.
- Saving the PCA loadings and factor scores to the prescribed locations.
- Logging variance explained and asserting the correct number of components.

The functions are deliberately lightweight and use only the standard
scientific‑Python stack already declared in ``requirements.txt``.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Tuple

import pandas as pd
from sklearn.decomposition import PCA

from code.logging_config import get_logger

__all__ = [
    "load_metrics_data",
    "run_pca_on_metrics",
    "save_pca_outputs",
    "run_pca_pipeline",
]


def load_metrics_data(csv_path: Path) -> pd.DataFrame:
    """Load the aggregated metrics CSV.

    Parameters
    ----------
    csv_path: Path
        Path to ``data/analysis/aggregated_metrics.csv`` produced by T022.

    Returns
    -------
    pd.DataFrame
        DataFrame containing the metrics.  The column ``subject_id`` is
        expected to be present; if it is missing the function will still
        return the DataFrame unchanged.
    """
    logger = get_logger(__name__)
    logger.info(f"Loading aggregated metrics from {csv_path}")
    if not csv_path.is_file():
        raise FileNotFoundError(f"Aggregated metrics file not found: {csv_path}")
    df = pd.read_csv(csv_path)
    if df.empty:
        raise ValueError(f"The aggregated metrics file {csv_path} is empty.")
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
    logger = get_logger(__name__)
    logger.info(f"Running PCA with {n_components} components")

    # Separate subject identifiers from the feature matrix
    if "subject_id" in df.columns:
        subject_ids = df["subject_id"].reset_index(drop=True)
        features = df.drop(columns=["subject_id"])
    else:
        logger.warning(
            "Column 'subject_id' not found in metrics; proceeding without it."
        )
        subject_ids = None
        features = df

    # Ensure numeric dtype
    features = features.apply(pd.to_numeric, errors="coerce")
    if features.isnull().any().any():
        raise ValueError("Non‑numeric values detected in metrics after conversion.")

    pca = PCA(n_components=n_components, svd_solver="full")
    scores_array = pca.fit_transform(features)

    # Loadings: components.T gives shape (n_features, n_components)
    loadings = pd.DataFrame(
        pca.components_.T,
        index=features.columns,
        columns=[f"PC{i+1}" for i in range(n_components)],
    )

    # Scores DataFrame
    scores = pd.DataFrame(
        scores_array,
        columns=[f"pca_factor_{i+1}" for i in range(n_components)],
    )
    if subject_ids is not None:
        scores.insert(0, "subject_id", subject_ids)

    # Log explained variance
    variance_explained = pca.explained_variance_ratio_
    logger.info(
        f"PCA variance explained (component 1..{n_components}): "
        f"{variance_explained.tolist()}"
    )
    return loadings, scores


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
    logger = get_logger(__name__)

    # Ensure parent directories exist
    loadings_path.parent.mkdir(parents=True, exist_ok=True)
    scores_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving PCA loadings to {loadings_path}")
    loadings.to_csv(loadings_path, index=True)

    logger.info(f"Saving PCA factor scores to {scores_path}")
    scores.to_csv(scores_path, index=False)


def run_pca_pipeline() -> None:
    """High‑level entry point used by ``code/analysis/correlations.py``.

    This function orchestrates the full PCA workflow required by task T023a.
    It is also safe to call directly (e.g. ``python -m code.analysis.pca_utils``)
    for debugging or ad‑hoc runs.
    """
    logger = get_logger(__name__)

    input_path = Path("data/analysis/aggregated_metrics.csv")
    loadings_path = Path("data/analysis/pca_loadings.csv")
    scores_path = Path("data/analysis/factor_scores.csv")

    df = load_metrics_data(input_path)
    loadings, scores = run_pca_on_metrics(df, n_components=2)

    # Assertion: exactly two components must be present
    assert (
        loadings.shape[1] == 2
    ), f"Expected 2 PCA components, got {loadings.shape[1]}"

    save_pca_outputs(loadings, scores, loadings_path, scores_path)

    logger.info("PCA pipeline completed successfully.")


if __name__ == "__main__":
    # Allow direct execution for quick testing
    run_pca_pipeline()
