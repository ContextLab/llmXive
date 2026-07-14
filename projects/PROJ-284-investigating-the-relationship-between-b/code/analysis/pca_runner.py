"""
Runner script for PCA analysis.
Invokes the PCA logic from code/analysis/correlations.py.
"""
import os
import sys
import logging
from pathlib import Path

from code.logging_config import get_logger
from code.analysis.correlations import load_metrics_data, run_pca_on_metrics, save_pca_results

logger = get_logger(__name__)

def main():
    """
    Execute PCA on network metrics and save results.
    """
    logger.log("pca_runner", step="start")
    
    try:
        # Load data
        df = load_metrics_data()
        
        # Run PCA
        pca_model, factor_scores = run_pca_on_metrics(df)
        
        # Save results
        save_pca_results(pca_model, factor_scores)
        
        logger.log("pca_runner", step="complete", success=True)
    except Exception as e:
        logger.log("pca_runner", step="error", error=str(e))
        raise

if __name__ == "__main__":
    main()
