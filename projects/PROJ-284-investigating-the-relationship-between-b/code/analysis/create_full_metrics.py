"""
Script to create full metrics file.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd
from code.logging_config import get_logger
from code.analysis.correlations import load_metrics_data, run_pca_on_metrics, generate_full_metrics

logger = get_logger(__name__)

def main():
    logger.log("create_full_metrics", status="starting")

    metrics_path = Path("data/analysis/aggregated_metrics.csv")
    if not metrics_path.exists():
        logger.log("create_full_metrics", status="failed", error="aggregated_metrics.csv not found.")
        return

    df = load_metrics_data(metrics_path)
    if df is None:
        return

    # Run PCA
    pca_scores = run_pca_on_metrics(df)

    # Generate full metrics
    generate_full_metrics(df, pca_scores)

    logger.log("create_full_metrics", status="completed")

if __name__ == "__main__":
    main()