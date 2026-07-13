import logging
from pathlib import Path
from typing import List

import pandas as pd
from sklearn.decomposition import PCA

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Existing functions from the original module are assumed to be present
# above this block (e.g., load_metrics_data, compute_and_save_pca, etc.).
# The implementations below add the missing pieces required for task
# T023b: merging raw metric columns with PCA factor scores and writing the
# combined DataFrame to disk.
# ----------------------------------------------------------------------


def load_metrics_data(metrics_path: Path = Path("data/analysis/metrics.csv")) -> pd.DataFrame:
    """
    Load the raw network metric data produced by earlier pipeline steps.

    Parameters
    ----------
    metrics_path : Path
        Path to the CSV file containing one row per subject with the
        individual network metrics (e.g., modularity, global_efficiency,
        participation_coef, within_module_degree). The file must contain a
        column named ``subject_id`` that uniquely identifies each subject.

    Returns
    -------
    pd.DataFrame
        DataFrame with the raw metric columns.
    """
    if not metrics_path.is_file():
        logger.error("Metrics file not found at %s", metrics_path)
        raise FileNotFoundError(f"Metrics file not found at {metrics_path}")

    df = pd.read_csv(metrics_path)
    logger.info("Loaded %d subjects with %d metric columns from %s",
                df.shape[0], df.shape[1] - 1, metrics_path)
    return df


def compute_and_save_pca(
    metrics_df: pd.DataFrame,
    n_components: int = 2,
    loadings_path: Path = Path("data/analysis/pca_loadings.csv"),
    scores_path: Path = Path("data/analysis/factor_scores.csv"),
) -> pd.DataFrame:
    """
    Perform PCA on the selected metric columns and persist both the loadings
    and the subject‑level factor scores.

    Parameters
    ----------
    metrics_df : pd.DataFrame
        DataFrame containing the raw metric columns. Must include a
        ``subject_id`` column that will be retained in the scores output.
    n_components : int, optional
        Number of principal components to retain (default 2).
    loadings_path : Path, optional
        Destination for the PCA loadings CSV.
    scores_path : Path, optional
        Destination for the subject‑level factor scores CSV.

    Returns
    -------
    pd.DataFrame
        DataFrame with ``subject_id`` and the PCA factor columns
        (e.g., ``pca_factor_1``, ``pca_factor_2``).
    """
    # Identify metric columns (exclude subject identifier)
    metric_cols = [c for c in metrics_df.columns if c != "subject_id"]
    if not metric_cols:
        raise ValueError("No metric columns found for PCA.")

    X = metrics_df[metric_cols].values
    pca = PCA(n_components=n_components, random_state=42)
    components = pca.fit_transform(X)

    # Save loadings: each component's weight for each original metric
    loadings = pd.DataFrame(
        pca.components_.T,
        index=metric_cols,
        columns=[f"component_{i+1}" for i in range(n_components)],
    )
    loadings_path.parent.mkdir(parents=True, exist_ok=True)
    loadings.to_csv(loadings_path, index_label="metric")
    logger.info("Saved PCA loadings to %s", loadings_path)

    # Save factor scores per subject
    scores = pd.DataFrame(
        components,
        columns=[f"pca_factor_{i+1}" for i in range(n_components)],
    )
    scores.insert(0, "subject_id", metrics_df["subject_id"].values)
    scores_path.parent.mkdir(parents=True, exist_ok=True)
    scores.to_csv(scores_path, index=False)
    logger.info("Saved PCA factor scores to %s", scores_path)

    return scores


def merge_metrics_and_pca_scores(
    metrics_df: pd.DataFrame, pca_scores_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge the raw metric columns with the PCA factor scores on ``subject_id``.

    Parameters
    ----------
    metrics_df : pd.DataFrame
        Raw metric data (must contain ``subject_id``).
    pca_scores_df : pd.DataFrame
        PCA factor scores (must contain ``subject_id``).

    Returns
    -------
    pd.DataFrame
        Combined DataFrame containing both raw metrics and PCA factors.
    """
    merged = pd.merge(metrics_df, pca_scores_df, on="subject_id", how="inner")
    logger.info(
        "Merged metrics (%d rows, %d cols) with PCA scores (%d rows, %d cols) -> %d rows, %d cols",
        metrics_df.shape[0],
        metrics_df.shape[1],
        pca_scores_df.shape[0],
        pca_scores_df.shape[1],
        merged.shape[0],
        merged.shape[1],
    )
    return merged


def save_full_metrics(
    full_df: pd.DataFrame,
    output_path: Path = Path("data/analysis/full_metrics.csv"),
) -> None:
    """
    Persist the combined metrics DataFrame to the declared output location.

    Parameters
    ----------
    full_df : pd.DataFrame
        DataFrame containing raw metrics and PCA factor columns.
    output_path : Path, optional
        Destination CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    full_df.to_csv(output_path, index=False)
    logger.info("Saved full metrics (raw + PCA) to %s", output_path)


def compute_and_save_correlation_matrix(
    full_metrics_path: Path = Path("data/analysis/full_metrics.csv"),
    correlation_output_path: Path = Path("data/analysis/correlation_matrix.csv"),
) -> None:
    """
    Compute a Pearson correlation matrix across all numeric columns in the
    full metrics file and write it to disk. This function is retained for
    backward compatibility with earlier pipeline stages.

    Parameters
    ----------
    full_metrics_path : Path
        CSV containing the merged metrics.
    correlation_output_path : Path
        Destination for the correlation matrix CSV.
    """
    if not full_metrics_path.is_file():
        logger.error("Full metrics file not found at %s", full_metrics_path)
        raise FileNotFoundError(f"Full metrics file not found at {full_metrics_path}")

    df = pd.read_csv(full_metrics_path)
    numeric_df = df.select_dtypes(include="number")
    corr = numeric_df.corr(method="pearson")
    correlation_output_path.parent.mkdir(parents=True, exist_ok=True)
    corr.to_csv(correlation_output_path)
    logger.info(
        "Computed Pearson correlation matrix and saved to %s", correlation_output_path
    )


def main() -> None:
    """
    End‑to‑end driver for T023b. It performs the following steps:

    1. Load raw metric data.
    2. Run PCA on the metric columns and write loadings / factor scores.
    3. Merge raw metrics with the factor scores.
    4. Persist the merged DataFrame as ``full_metrics.csv``.
    5. (Optional) Compute a correlation matrix for downstream steps.

    The function is deliberately lightweight so that it can be invoked
    directly from the run‑book (``python -m code.analysis.correlations``) or
    via the higher‑level ``correlation_main_runner``.
    """
    logger.info("Starting T023b – merge metrics with PCA scores")

    # 1. Load raw metrics
    metrics_df = load_metrics_data()

    # 2. Compute PCA and persist loadings / scores
    pca_scores_df = compute_and_save_pca(metrics_df)

    # 3. Merge raw metrics with PCA scores
    full_df = merge_metrics_and_pca_scores(metrics_df, pca_scores_df)

    # 4. Save the combined DataFrame
    save_full_metrics(full_df)

    # 5. Compute and store correlation matrix (used by later visualisation steps)
    compute_and_save_correlation_matrix()

    logger.info("T023b completed successfully")
