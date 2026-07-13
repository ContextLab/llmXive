"""
Utility module used by the CI validation step to confirm that the dynamic
batch‑size logic behaves as expected.  The original implementation generated
synthetic NIfTI‑like data, which violated the “real data only” policy.

This revised version **does not create synthetic neuroimaging files**.  Instead,
it works with tiny CSV files that are already part of the repository
(e.g. ``data/analysis/metrics.csv``).  The functions now simply verify that
the batch‑size calculator returns a sensible integer and that the preprocessing
and correlation pipelines can be invoked on a minimal real dataset.
"""

import logging
import os
from pathlib import Path

from analysis.correlations import (
    calculate_batch_size,
    load_metrics_data,
    run_pca_analysis,
    merge_metrics_and_pca_scores,
)

logger = logging.getLogger(__name__)


def verify_batch_size_logic() -> None:
    """
    Simple sanity‑check: ensure that the batch size calculation returns a
    positive integer that does not exceed the number of subjects in the
    real metrics file.
    """
    metrics_path = Path("data/analysis/metrics.csv")
    metrics_df = load_metrics_data(metrics_path)
    n_subjects = len(metrics_df)
    batch = calculate_batch_size(n_subjects)
    assert isinstance(batch, int) and batch > 0, "Batch size must be a positive integer"
    assert batch <= n_subjects, "Batch size cannot exceed number of subjects"
    logger.info("Batch size verification passed (batch=%d, subjects=%d)", batch, n_subjects)


def verify_preprocessing_batching() -> None:
    """
    Verify that the preprocessing‑batching step can be called without
    generating synthetic NIfTI data.  The function simply calls the merge
    routine with the real metric dataframe and the PCA scores that were
    produced by ``run_pca_analysis``.
    """
    metrics_path = Path("data/analysis/metrics.csv")
    metrics_df = load_metrics_data(metrics_path)
    _, pca_scores_df = run_pca_analysis(metrics_df)
    # This will write ``full_metrics.csv`` – the existence of the file is the
    # success criterion.
    merge_metrics_and_pca_scores(metrics_df, pca_scores_df)
    full_path = Path("data/analysis/full_metrics.csv")
    assert full_path.is_file(), "full_metrics.csv was not created"
    logger.info("Preprocessing batching verification succeeded")


def verify_correlation_batching() -> None:
    """
    Run a minimal correlation analysis on the merged dataset to ensure that
    the pipeline works end‑to‑end with real data.
    """
    from analysis.correlations import (
        run_correlation_analysis,
        apply_fdr_correction,
    )

    merged_path = Path("data/analysis/full_metrics.csv")
    if not merged_path.is_file():
        raise FileNotFoundError("full_metrics.csv missing for correlation verification")
    merged_df = pd.read_csv(merged_path)
    corr_df = run_correlation_analysis(merged_df, covariate="MeanFD")
    _ = apply_fdr_correction(corr_df)  # just ensure it runs without error
    logger.info("Correlation batching verification succeeded")


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    verify_batch_size_logic()
    verify_preprocessing_batching()
    verify_correlation_batching()
    logger.info("All batching verification steps passed")


if __name__ == "__main__":
    main()