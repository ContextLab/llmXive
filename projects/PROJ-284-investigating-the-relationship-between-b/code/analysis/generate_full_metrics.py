"""
Script to generate full_metrics.csv by merging metrics and PCA scores.
This is the runner script invoked by the pipeline to ensure T023b output is produced.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.logging_config import get_logger
from code.analysis.correlations import (
    load_metrics_data,
    compute_and_save_pca,
    merge_metrics_and_pca_scores,
    save_full_metrics
)

logger = get_logger(__name__)

def merge_and_save_full_metrics():
    """
    Orchestrates the loading, PCA, merging, and saving of full metrics.
    This function is called by main() below.
    """
    logger.log("merge_and_save_full_metrics", start=True)
    
    # 1. Load aggregated metrics
    try:
        metrics_df = load_metrics_data()
        logger.log("merge_and_save_full_metrics", metrics_loaded=len(metrics_df))
    except FileNotFoundError as e:
        logger.log("merge_and_save_full_metrics", error=str(e), status="failed")
        raise
    
    # 2. Compute PCA (saves factor_scores.csv and pca_loadings.csv)
    try:
        loadings_df, pca_scores_df = compute_and_save_pca(metrics_df)
        logger.log("merge_and_save_full_metrics", pca_computed=True)
    except Exception as e:
        logger.log("merge_and_save_full_metrics", error=str(e), status="failed")
        raise
    
    # 3. Merge
    try:
        merged_df = merge_metrics_and_pca_scores(metrics_df, pca_scores_df)
        logger.log("merge_and_save_full_metrics", merged_count=len(merged_df))
    except Exception as e:
        logger.log("merge_and_save_full_metrics", error=str(e), status="failed")
        raise
    
    # 4. Save
    try:
        output_path = save_full_metrics(merged_df)
        logger.log("merge_and_save_full_metrics", output_path=output_path, status="success")
        return output_path
    except Exception as e:
        logger.log("merge_and_save_full_metrics", error=str(e), status="failed")
        raise

def main():
    """
    Entry point for the script.
    """
    logger.log("main", script="generate_full_metrics.py")
    try:
        path = merge_and_save_full_metrics()
        print(f"Successfully generated: {path}")
    except Exception as e:
        logger.log("main", status="failed", error=str(e))
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
