"""
Standalone runner for T023a: Run PCA and save loadings/scores.
Ensures data/analysis/pca_loadings.csv and data/analysis/factor_scores.csv are written.
"""
import os
import sys
import logging
from pathlib import Path
from code.analysis.correlations import load_metrics_data, run_pca_on_metrics
from code.logging_config import get_logger

logger = get_logger(__name__)

def main() -> None:
    """
    Entry point for the PCA runner script.
    """
    logger.log("pca_runner", step="start")
    
    metrics_path = "data/processed/aggregated_metrics.csv"
    loadings_path = "data/analysis/pca_loadings.csv"
    scores_path = "data/analysis/factor_scores.csv"

    if not Path(metrics_path).exists():
        logger.log("pca_runner", error=f"Input file not found: {metrics_path}")
        print(f"Error: {metrics_path} not found.")
        sys.exit(1)

    try:
        df = load_metrics_data(metrics_path)
        logger.log("pca_runner", step="executing_pca", rows=len(df))
        
        loadings_df, scores_df = run_pca_on_metrics(
            df,
            output_loadings_path=loadings_path,
            output_scores_path=scores_path
        )
        
        print(f"PCA completed.")
        print(f"Loadings saved to: {loadings_path}")
        print(f"Scores saved to: {scores_path}")
        
    except Exception as e:
        logger.log("pca_runner", error=str(e))
        raise

if __name__ == "__main__":
    main()
