"""
Script to generate the full_metrics.csv file.
This script merges raw metrics with PCA factor scores.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd
from code.logging_config import get_logger
from code.analysis.correlations import main as correlations_main

logger = get_logger(__name__)

def generate_full_metrics():
    """
    Loads individual metrics and PCA scores, merges them, and saves to data/analysis/full_metrics.csv.
    """
    logger.log("generate_full_metrics_start")
    
    # Define paths
    metrics_path = "data/processed/aggregated_metrics.csv"
    pca_scores_path = "data/analysis/factor_scores.csv"
    output_path = "data/analysis/full_metrics.csv"
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Load data
    if not os.path.exists(metrics_path):
        logger.log("generate_full_metrics_error", reason=f"File not found: {metrics_path}")
        raise FileNotFoundError(f"Required file not found: {metrics_path}")
    
    if not os.path.exists(pca_scores_path):
        logger.log("generate_full_metrics_error", reason=f"File not found: {pca_scores_path}")
        raise FileNotFoundError(f"Required file not found: {pca_scores_path}")
    
    df_metrics = pd.read_csv(metrics_path)
    df_pca = pd.read_csv(pca_scores_path)
    
    # Merge on subject_id
    # Ensure column names match
    if 'subject_id' in df_metrics.columns and 'subject_id' in df_pca.columns:
        df_full = pd.merge(df_metrics, df_pca, on='subject_id', how='outer')
    else:
        # Fallback if column names differ (e.g., 'Subject' vs 'subject_id')
        # Try to find a common key
        common_keys = set(df_metrics.columns).intersection(set(df_pca.columns))
        if common_keys:
            key = list(common_keys)[0]
            df_full = pd.merge(df_metrics, df_pca, on=key, how='outer')
        else:
            logger.log("generate_full_metrics_error", reason="No common key found to merge metrics and PCA scores")
            raise ValueError("No common key found to merge metrics and PCA scores")
    
    # Save
    df_full.to_csv(output_path, index=False)
    logger.log("generate_full_metrics_complete", output=output_path, rows=len(df_full))
    return output_path

def main():
    generate_full_metrics()

if __name__ == "__main__":
    main()
