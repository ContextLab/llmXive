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
from code.analysis.correlations import load_metrics_data, run_pca_on_metrics, generate_full_metrics, save_full_metrics

logger = get_logger(__name__)

def main():
    """
    Combine raw metrics and PCA scores into a single file.
    """
    logger.log("create_full_metrics", step="start")
    
    try:
        # Load raw metrics
        df_metrics = load_metrics_data()
        
        # Run PCA to get scores
        _, df_pca = run_pca_on_metrics(df_metrics)
        
        # Generate and save full metrics
        df_full = generate_full_metrics(df_metrics, df_pca)
        save_full_metrics(df_full)
        
        logger.log("create_full_metrics", step="complete", success=True)
    except Exception as e:
        logger.log("create_full_metrics", step="error", error=str(e))
        raise

if __name__ == "__main__":
    main()
