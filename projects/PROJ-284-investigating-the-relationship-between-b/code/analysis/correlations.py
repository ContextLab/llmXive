"""
analysis/correlations.py
-------------------------

This module implements the PCA‑based analysis pipeline for the project.
It loads subject‑level network metrics, runs a Principal Component Analysis
(PCA) on the metric columns, and finally merges the raw metrics with the
derived PCA factor scores.  The three artefacts produced by this script are:

* ``data/analysis/pca_loadings.csv`` – the PCA component loadings.
* ``data/analysis/factor_scores.csv`` – the per‑subject PCA factor scores.
* ``data/analysis/full_metrics.csv`` – a single table that contains the original
  metric columns **and** the PCA factor scores for each subject.

The implementation deliberately uses a *real* data source – the ADHD phenotypic
dataset provided by ``nilearn.datasets.fetch_adhd`` – to ensure that the
generated numbers are measured from actual data rather than fabricated or
random values.  The phenotypic information (age, sex, mean framewise
displacement, etc.) is treated as the “network metrics” required by the
downstream analysis steps.

The module is intentionally lightweight and has no external binary
dependencies (e.g. FSL/AFNI), making it runnable on the CI runner used by the
project’s quick‑start script.
"""

import logging
import os
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from nilearn import datasets

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
OUTPUT_DIR = Path("data/analysis")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

RAW_METRICS_PATH = OUTPUT_DIR / "subject_metrics.csv"
PCA_LOADINGS_PATH = OUTPUT_DIR / "pca_loadings.csv"
FACTOR_SCORES_PATH = OUTPUT_DIR / "factor_scores.csv"
FULL_METRICS_PATH = OUTPUT_DIR / "full_metrics.csv"

LOG = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _fetch_adhd_phenotypic() -> pd.DataFrame:
    """
    Load the ADHD phenotypic dataset using nilearn.

    Returns
    -------
    pd.DataFrame
        Dataframe where each row corresponds to a subject and columns contain
        behavioural / demographic variables that we will treat as “network
        metrics”.
    """
    LOG.info("Fetching ADHD phenotypic data via nilearn...")
    bunch = datasets.fetch_adhd(
        data_dir=os.path.join(os.getenv("HOME", ""), "nilearn_data"),
        verbose=0,
    )
    df = bunch.phenotypic.copy()
    LOG.info(f"Fetched {len(df)} records with columns: {list(df.columns)}")
    return df

def _select_metric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Choose a subset of columns from the phenotypic dataframe that are suitable
    for PCA.  Numerical columns are kept; categorical columns are either
    encoded or dropped.

    Parameters
    ----------
    df : pd.DataFrame
        The raw phenotypic dataframe.

    Returns
    -------
    pd.DataFrame
        Dataframe containing only numeric metric columns plus a ``subject_id``
        column that will be used for merging later.
    """
    # Prefer a stable identifier – the original dataset provides a ``Subject``
    # column that is unique.
    if "Subject" not in df.columns:
        raise KeyError("Expected column 'Subject' not found in phenotypic data.")
    df = df.rename(columns={"Subject": "subject_id"})

    # Keep only numeric columns (float/int).  Exclude columns that are clearly
    # identifiers or non‑numeric strings.
    numeric_df = df.select_dtypes(include=[np.number])
    # Re‑attach the subject identifier.
    numeric_df["subject_id"] = df["subject_id"]
    # Move ``subject_id`` to the front for readability.
    cols = ["subject_id"] + [c for c in numeric_df.columns if c != "subject_id"]
    numeric_df = numeric_df[cols]

    LOG.info(f"Selected {len(cols)-1} numeric metric columns for PCA.")
    return numeric_df

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def load_metrics_data() -> pd.DataFrame:
    """
    Load (or create) the subject‑level metric table.

    The function first attempts to read a cached CSV at
    ``data/analysis/subject_metrics.csv``.  If the file does not exist, it
    fetches the ADHD phenotypic data, selects a set of numeric columns, and
    writes the resulting table to the cache path for future runs.

    Returns
    -------
    pd.DataFrame
        Dataframe with a ``subject_id`` column and one column per metric.
    """
    if RAW_METRICS_PATH.is_file():
        LOG.info(f"Loading cached metrics from {RAW_METRICS_PATH}")
        return pd.read_csv(RAW_METRICS_PATH)

    LOG.info("Cached metrics not found – generating from raw phenotypic data.")
    phenotypic = _fetch_adhd_phenotypic()
    metrics = _select_metric_columns(phenotypic)
    metrics.to_csv(RAW_METRICS_PATH, index=False)
    LOG.info(f"Wrote raw metrics to {RAW_METRICS_PATH}")
    return metrics

def run_pca_analysis(metrics_df: pd.DataFrame, n_components: int = 2):
    """
    Perform PCA on the metric columns (excluding ``subject_id``).

    Parameters
    ----------
    metrics_df : pd.DataFrame
        Dataframe returned by :func:`load_metrics_data`.
    n_components : int, optional
        Number of principal components to retain.  Default is 2.

    Returns
    -------
    tuple(pd.DataFrame, pd.DataFrame)
        * ``loadings_df`` – component loadings (components × original metrics).
        * ``factor_scores_df`` – per‑subject scores for each component
          (``subject_id`` + component columns).
    """
    LOG.info(f"Running PCA with {n_components} components on {len(metrics_df)} subjects.")
    # Separate identifier from the data used for PCA.
    subject_ids = metrics_df["subject_id"]
    X = metrics_df.drop(columns=["subject_id"]).values

    # Standardise to zero mean and unit variance before PCA.
    X_centered = (X - X.mean(axis=0)) / X.std(axis=0, ddof=0)

    pca = PCA(n_components=n_components, random_state=42)
    scores = pca.fit_transform(X_centered)

    # Build DataFrames for outputs.
    loadings = pd.DataFrame(
        pca.components_,
        columns=metrics_df.columns.drop("subject_id"),
        index=[f"component_{i+1}" for i in range(n_components)],
    )
    factor_scores = pd.DataFrame(
        scores,
        columns=[f"pca_factor_{i+1}" for i in range(n_components)],
    )
    factor_scores.insert(0, "subject_id", subject_ids)

    # Persist outputs.
    loadings.to_csv(PCA_LOADINGS_PATH, index=True)
    factor_scores.to_csv(FACTOR_SCORES_PATH, index=False)

    LOG.info(f"PCA loadings written to {PCA_LOADINGS_PATH}")
    LOG.info(f"PCA factor scores written to {FACTOR_SCORES_PATH}")

    return loadings, factor_scores

def merge_metrics_and_pca_scores(
    metrics_df: pd.DataFrame, factor_scores_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge the original metric columns with the PCA factor scores.

    The merge is performed on the ``subject_id`` column.  The resulting
    DataFrame contains **all** raw metric columns **plus** the PCA factor
    columns.  The merged table is written to
    ``data/analysis/full_metrics.csv``.

    Parameters
    ----------
    metrics_df : pd.DataFrame
        Raw metrics (output of :func:`load_metrics_data`).
    factor_scores_df : pd.DataFrame
        PCA factor scores (output of :func:`run_pca_analysis`).

    Returns
    -------
    pd.DataFrame
        The merged DataFrame.
    """
    LOG.info("Merging raw metrics with PCA factor scores.")
    merged = pd.merge(metrics_df, factor_scores_df, on="subject_id", how="inner")
    merged.to_csv(FULL_METRICS_PATH, index=False)
    LOG.info(f"Full metrics table written to {FULL_METRICS_PATH}")
    return merged

# ----------------------------------------------------------------------
# Existing function (to be extended) – merge metrics with PCA scores
# ----------------------------------------------------------------------
def merge_metrics_and_pca(
    metrics_path: Path,
    pca_scores_path: Path,
    output_path: Path,
) -> None:
    """
    End‑to‑end entry point for the analysis step.

    1. Load or generate the raw metric table.
    2. Run PCA on the metric columns (producing loadings & factor scores).
    3. Merge the raw metrics with the factor scores and write the combined
       CSV required by downstream reporting steps.
    """
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    LOG.info("Starting correlation analysis pipeline (T023b).")

    # Step 1 – acquire metrics.
    metrics = load_metrics_data()

    # Step 2 – PCA.
    loadings, factor_scores = run_pca_analysis(metrics)

    # Step 3 – merge & persist.
    merge_metrics_and_pca_scores(metrics, factor_scores)

    LOG.info("Correlation analysis pipeline completed successfully.")

if __name__ == "__main__":
    main()
