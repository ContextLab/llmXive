import os
import sys
import logging
from pathlib import Path

from code.logging_config import get_logger
from code.analysis.correlations import perform_pca_on_metrics, load_metrics_data, save_pca_results

logger = get_logger(__name__)

def main() -> None:
    """Run PCA on metrics and save results."""
    logger.log("pca_runner", step="start")
    
    try:
        # Load data
        metrics_df = load_metrics_data()
        logger.log("pca_runner", n_rows=len(metrics_df))
        
        # Define metric columns
        metric_cols = ['modularity', 'global_efficiency', 'participation_coef', 'within_module_degree']
        
        # Perform PCA
        pca, loadings, scores = perform_pca_on_metrics(metrics_df)
        logger.log("pca_runner", n_components=len(scores[0]))
        
        # Save results
        save_pca_results(loadings, scores, metrics_df, pca, metric_cols)
        logger.log("pca_runner", step="complete")
        
    except Exception as e:
        logger.log("pca_runner", error=str(e))
        raise

if __name__ == "__main__":
    main()
