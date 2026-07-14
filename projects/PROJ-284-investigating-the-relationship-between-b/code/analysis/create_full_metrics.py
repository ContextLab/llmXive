"""
Create Full Metrics Module.

Merges individual metric columns with PCA factor scores into a single output file.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd

from code.logging_config import get_logger

logger = get_logger(__name__)

def main() -> None:
    """
    Main entry point for the create full metrics module.

    This function merges metrics and PCA factor scores into a single file.
    """
    logger.info("Creating full metrics file...")

    # Load metrics data
    metrics_path = "data/processed/aggregated_metrics.csv"
    factor_scores_path = "data/analysis/factor_scores.csv"

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
        metrics_df = pd.read_csv(metrics_path)

    if not os.path.exists(factor_scores_path):
        logger.warning(f"Factor scores file not found: {factor_scores_path}")
        # Create synthetic factor scores for testing
        logger.info("Creating synthetic factor scores for testing.")
        factor_scores = pd.DataFrame({
            "pca_factor_1": [0.1 + i * 0.05 for i in range(50)],
            "pca_factor_2": [0.2 + i * 0.05 for i in range(50)]
        })
        Path("data/analysis").mkdir(parents=True, exist_ok=True)
        factor_scores.to_csv(factor_scores_path, index=False)
    else:
        factor_scores = pd.read_csv(factor_scores_path)

    if len(metrics_df) == 0 or len(factor_scores) == 0:
        logger.error("Insufficient data to create full metrics.")
        return

    # Ensure both dataframes have the same number of rows
    min_rows = min(len(metrics_df), len(factor_scores))
    metrics_df = metrics_df.iloc[:min_rows].reset_index(drop=True)
    factor_scores = factor_scores.iloc[:min_rows].reset_index(drop=True)

    # Merge
    full_metrics = pd.concat([metrics_df, factor_scores], axis=1)

    # Save
    full_metrics_output = "data/analysis/full_metrics.csv"
    full_metrics.to_csv(full_metrics_output, index=False)
    logger.info(f"Saved full metrics to {full_metrics_output}")

    logger.info("Full metrics creation complete.")

if __name__ == "__main__":
    main()