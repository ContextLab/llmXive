"""
Script to generate full_metrics.csv by merging raw metrics and PCA scores.
This script is invoked by the run-book to ensure T023b deliverables are produced.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd
from code.logging_config import get_logger
from code.analysis.correlations import perform_pca_on_metrics, generate_full_metrics, save_pca_results

logger = get_logger(__name__)

def main() -> None:
    """
    Entry point for generating full metrics.
    1. Load aggregated metrics.
    2. Perform PCA.
    3. Merge and save full_metrics.csv.
    """
    logger.log("generate_full_metrics_start")
    
    metrics_path = Path("data/processed/aggregated_metrics.csv")
    if not metrics_path.exists():
        logger.log("generate_full_metrics_error", {"message": "aggregated_metrics.csv not found"})
        sys.exit(1)
    
    # Load
    metrics_df = pd.read_csv(metrics_path)
    logger.log("generate_full_metrics_loaded", {"rows": len(metrics_df)})
    
    # Identify metric columns
    exclude = {"subject_id", "age", "sex", "fd", "motor_score"}
    metric_cols = [c for c in metrics_df.columns if c not in exclude]
    
    if not metric_cols:
        logger.log("generate_full_metrics_error", {"message": "No metric columns found"})
        sys.exit(1)
    
    # PCA
    loadings, scores = perform_pca_on_metrics(metrics_df, metric_cols)
    save_pca_results(loadings, scores)
    
    # Ensure scores has subject_id for merge
    if "subject_id" not in scores.columns:
        if metrics_df["subject_id"].nunique() == scores.index.nunique():
            scores = scores.reset_index()
            scores.rename(columns={scores.columns[0]: "subject_id"}, inplace=True)
        else:
            logger.log("generate_full_metrics_error", {"message": "Subject ID mismatch in scores"})
            sys.exit(1)
    
    # Merge
    full_df = generate_full_metrics(metrics_df, scores)
    
    if full_df.empty:
        logger.log("generate_full_metrics_error", {"message": "Merge resulted in empty dataframe"})
        sys.exit(1)
        
    logger.log("generate_full_metrics_success", {"rows": len(full_df)})

if __name__ == "__main__":
    main()
