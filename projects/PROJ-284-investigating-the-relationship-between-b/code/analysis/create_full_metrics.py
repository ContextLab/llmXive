import os
import sys
import logging
from pathlib import Path
import pandas as pd

from code.logging_config import get_logger
from code.analysis.correlations import (
    load_metrics_data, 
    perform_pca_on_metrics, 
    save_pca_results, 
    generate_full_metrics, 
    save_full_metrics
)

logger = get_logger(__name__)

def main() -> None:
    """
    Main entry point to create full metrics (raw + PCA).
    Writes:
      - data/analysis/factor_scores.csv
      - data/analysis/pca_loadings.csv
      - data/analysis/full_metrics.csv
    """
    logger.log("create_full_metrics_start")
    
    try:
        # 1. Load aggregated metrics
        metrics_df = load_metrics_data()
        logger.log("metrics_loaded", rows=len(metrics_df))
        
        # 2. Perform PCA
        loadings, factor_scores = perform_pca_on_metrics(metrics_df)
        logger.log("pca_performed", n_components=loadings.shape[1])
        
        # 3. Save PCA results (creates factor_scores.csv and pca_loadings.csv)
        save_pca_results(loadings, factor_scores)
        logger.log("pca_results_saved")
        
        # 4. Generate full metrics (merge raw + PCA)
        full_df = generate_full_metrics(metrics_df, factor_scores)
        logger.log("full_metrics_generated", rows=len(full_df))
        
        # 5. Save full metrics
        save_full_metrics(full_df)
        logger.log("full_metrics_saved")
        
        logger.log("create_full_metrics_complete")
        
    except Exception as e:
        logger.log("create_full_metrics_error", error=str(e))
        raise

if __name__ == "__main__":
    main()
