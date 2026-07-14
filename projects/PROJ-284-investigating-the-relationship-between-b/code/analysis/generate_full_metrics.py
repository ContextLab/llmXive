"""
Runner script for generating full metrics file (T023b).
Merges raw metrics with PCA scores and saves to data/analysis/full_metrics.csv.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from code.logging_config import get_logger
from code.analysis.correlations import (
    load_metrics_data, 
    compute_and_save_pca, 
    merge_metrics_and_pca_scores, 
    save_full_metrics
)

logger = get_logger(__name__)

def main():
    logger.log("generate_full_metrics", step="start")
    
    metrics_path = "data/processed/aggregated_metrics.csv"
    output_path = "data/analysis/full_metrics.csv"
    
    if not Path(metrics_path).exists():
        logger.log("generate_full_metrics", error=f"Metrics file not found: {metrics_path}")
        raise FileNotFoundError(f"Required input file missing: {metrics_path}")
    
    # Load metrics
    df_metrics = load_metrics_data(metrics_path)
    
    # Ensure PCA is done
    loadings, scores = compute_and_save_pca(df_metrics)
    
    # Merge
    df_full = merge_metrics_and_pca_scores(df_metrics, scores)
    
    # Save
    save_full_metrics(df_full, output_path)
    
    logger.log("generate_full_metrics", step="complete", output=output_path)

if __name__ == "__main__":
    main()
