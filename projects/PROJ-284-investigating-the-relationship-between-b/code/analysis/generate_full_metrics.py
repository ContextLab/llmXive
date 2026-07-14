"""
Script to generate the full metrics file combining raw metrics and PCA scores.
This ensures data/analysis/full_metrics.csv is produced.
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
    logger.log("generate_full_metrics", step="start")
    try:
        # Load base metrics
        metrics_df = load_metrics_data()
        
        # Run PCA to get scores
        _, scores_df = run_pca_on_metrics(metrics_df)
        
        # Generate the combined file
        generate_full_metrics(scores_df, metrics_df)
        
        logger.log("generate_full_metrics", step="completed")
    except Exception as e:
        logger.log("generate_full_metrics", step="failed", error=str(e))
        raise

if __name__ == "__main__":
    main()