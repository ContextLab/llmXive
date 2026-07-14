"""Run PCA analysis on real metrics data."""
import os
import sys
import logging
from pathlib import Path
import pandas as pd
from code.logging_config import get_logger
from code.analysis.correlations import run_pca, load_metrics_data, compute_and_save_pca

logger = get_logger(__name__)


def main():
    """Main entry point for PCA runner."""
    logger.info("Starting PCA analysis")

    # Load metrics
    metrics_path = 'data/processed/aggregated_metrics.csv'
    if not os.path.exists(metrics_path):
        logger.error(f"Metrics file not found: {metrics_path}")
        logger.info("Run create_full_metrics.py first")
        return

    try:
        metrics_df = load_metrics_data(metrics_path)
        output_dir = 'data/analysis'
        os.makedirs(output_dir, exist_ok=True)

        # Compute and save PCA
        pca_scores = compute_and_save_pca(metrics_df, output_dir)
        logger.info(f"PCA analysis complete: {len(pca_scores)} scores computed")

    except Exception as e:
        logger.error(f"PCA analysis failed: {e}")
        raise


if __name__ == '__main__':
    main()
