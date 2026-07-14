"""
Standalone runner for T023b: Merge metrics and PCA scores.
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
    logger.log("generate_full_metrics", step="start")
    
    metrics_path = "data/processed/aggregated_metrics.csv"
    loadings_path = "data/analysis/pca_loadings.csv"
    scores_path = "data/analysis/factor_scores.csv"
    full_metrics_path = "data/analysis/full_metrics.csv"

    if not Path(metrics_path).exists():
        logger.log("generate_full_metrics", error=f"Input file not found: {metrics_path}")
        print(f"Error: {metrics_path} not found.")
        sys.exit(1)

    try:
        df = load_metrics_data(metrics_path)
        
        # Ensure PCA files exist (run them if not)
        if not Path(scores_path).exists():
            logger.log("generate_full_metrics", step="running_pca")
            loadings_df, scores_df = run_pca_on_metrics(
                df,
                output_loadings_path=loadings_path,
                output_scores_path=scores_path
            )
        else:
            # Load existing scores if they exist
            scores_df = pd.read_csv(scores_path)
            logger.log("generate_full_metrics", step="loading_existing_scores")

        # Generate full metrics
        logger.log("generate_full_metrics", step="merging")
        full_df = generate_full_metrics(df, scores_df, output_path=full_metrics_path)
        
        print(f"Successfully wrote {full_metrics_path}")
        
    except Exception as e:
        logger.log("generate_full_metrics", error=str(e))
        raise

if __name__ == "__main__":
    main()