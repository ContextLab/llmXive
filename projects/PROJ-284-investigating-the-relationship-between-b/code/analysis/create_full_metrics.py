"""
Standalone runner for T023b: Generate full metrics CSV.
Ensures data/analysis/full_metrics.csv is written.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd
from code.logging_config import get_logger
from code.analysis.correlations import load_metrics_data, run_pca_on_metrics, generate_full_metrics

logger = get_logger(__name__)

def main() -> None:
    """
    Entry point for the full metrics generation script.
    """
    logger.log("create_full_metrics", step="start")
    
    metrics_path = "data/processed/aggregated_metrics.csv"
    loadings_path = "data/analysis/pca_loadings.csv"
    scores_path = "data/analysis/factor_scores.csv"
    full_metrics_path = "data/analysis/full_metrics.csv"

    # Check if input exists
    if not Path(metrics_path).exists():
        logger.log("create_full_metrics", error=f"Input file not found: {metrics_path}")
        print(f"Error: {metrics_path} not found. Please run the preprocessing pipeline first.")
        sys.exit(1)

    try:
        # Load
        df = load_metrics_data(metrics_path)
        
        # PCA
        logger.log("create_full_metrics", step="pca")
        loadings_df, scores_df = run_pca_on_metrics(
            df,
            output_loadings_path=loadings_path,
            output_scores_path=scores_path
        )
        
        # Merge & Save
        logger.log("create_full_metrics", step="merge")
        full_df = generate_full_metrics(df, scores_df, output_path=full_metrics_path)
        
        print(f"Successfully wrote {full_metrics_path} with {len(full_df)} rows.")
        
    except Exception as e:
        logger.log("create_full_metrics", error=str(e))
        raise

if __name__ == "__main__":
    main()
