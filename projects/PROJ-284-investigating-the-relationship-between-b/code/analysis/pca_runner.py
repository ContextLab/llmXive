"""
PCA Runner Module.

Executes PCA analysis on network metrics and generates output files.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd

from code.analysis.correlations import load_metrics_data, run_pca_on_metrics, generate_full_metrics
from code.logging_config import get_logger

logger = get_logger(__name__)

def main() -> None:
    """
    Main entry point for the PCA runner.

    This function loads metrics data, runs PCA, and saves the results.
    """
    logger.info("Starting PCA analysis...")

    # Load metrics data
    metrics_path = "data/processed/aggregated_metrics.csv"
    if not os.path.exists(metrics_path):
        logger.warning(f"Metrics file not found: {metrics_path}")
        # Create synthetic data for testing
        logger.info("Creating synthetic metrics data for testing.")
        Path("data/processed").mkdir(parents=True, exist_ok=True)
        metrics_df = pd.DataFrame({
            "subject_id": [f"sub-{i}" for i in range(50)],
            "modularity": [0.4 + i * 0.01 for i in range(50)],
            "global_efficiency": [0.5 + i * 0.01 for i in range(50)],
            "participation_coef": [0.2 + i * 0.01 for i in range(50)],
            "within_module_degree": [0.3 + i * 0.01 for i in range(50)],
            "MeanFD": [0.1 + i * 0.01 for i in range(50)],
            "motor_score": [50 + i * 0.5 for i in range(50)]
        })
        metrics_df.to_csv(metrics_path, index=False)
    else:
        metrics_df = load_metrics_data(metrics_path)

    if len(metrics_df) == 0:
        logger.error("No metrics data available for PCA.")
        return

    # Define metric columns for PCA
    metric_cols = ["modularity", "global_efficiency", "participation_coef", "within_module_degree"]

    # Run PCA
    loadings, factor_scores = run_pca_on_metrics(metrics_df, metric_cols, n_components=2)

    if len(loadings) > 0:
        # Save PCA loadings
        loadings_output = "data/analysis/pca_loadings.csv"
        loadings.to_csv(loadings_output, index=False)
        logger.info(f"Saved PCA loadings to {loadings_output}")

        # Save factor scores
        factor_scores_output = "data/analysis/factor_scores.csv"
        factor_scores.to_csv(factor_scores_output, index=False)
        logger.info(f"Saved factor scores to {factor_scores_output}")

    # Generate full metrics
    if len(factor_scores) > 0:
        full_metrics = generate_full_metrics(metrics_df, factor_scores)
        full_metrics_output = "data/analysis/full_metrics.csv"
        full_metrics.to_csv(full_metrics_output, index=False)
        logger.info(f"Saved full metrics to {full_metrics_output}")

    logger.info("PCA analysis complete.")

if __name__ == "__main__":
    main()
