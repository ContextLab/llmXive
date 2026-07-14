import os
import sys
import logging
from pathlib import Path
from code.analysis.correlations import load_metrics_data, run_pca_on_metrics, generate_full_metrics
from code.logging_config import get_logger

logger = get_logger(__name__)

def main() -> None:
    """
    Runner script to execute PCA and generate full metrics.
    This script is invoked by the run-book to ensure T023a and T023b outputs are generated.
    """
    logger.log("pca_runner", step="T023a/T023b", status="started")
    try:
        # Load data
        metrics_df = load_metrics_data()
        
        # Run PCA
        loadings_df, factor_scores_df = run_pca_on_metrics(metrics_df)
        
        # Generate full metrics (merging raw + PCA)
        full_df = generate_full_metrics(metrics_df, factor_scores_df)
        
        logger.log("pca_runner", step="T023a/T023b", status="completed")
    except Exception as e:
        logger.log("pca_runner", step="T023a/T023b", status="failed", error=str(e))
        raise

if __name__ == "__main__":
    main()
