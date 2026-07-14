import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from code.logging_config import get_logger
from code.analysis.correlations import load_metrics_data, perform_pca_on_metrics, save_pca_results, merge_metrics_with_pca_scores, generate_full_metrics_output

logger = get_logger(__name__)

def main():
    """
    Standalone runner for T023b: Generate full metrics output.
    Merges raw metrics with PCA scores and saves to data/analysis/full_metrics.csv.
    """
    logger.log("generate_full_metrics", status="starting")
    
    try:
        # Load raw metrics
        metrics_df = load_metrics_data()
        
        # Perform PCA if not already done (or reload scores if they exist)
        scores_path = Path("data/analysis/factor_scores.csv")
        if scores_path.exists():
            scores_df = pd.read_csv(scores_path)
        else:
            _, _, scores_df = perform_pca_on_metrics(metrics_df)
            save_pca_results(pd.DataFrame(), scores_df) # Save only scores if loadings not needed separately here
        
        # Merge
        merged_df = merge_metrics_with_pca_scores(metrics_df, scores_df)
        
        # Output
        generate_full_metrics_output(merged_df)
        
        logger.log("generate_full_metrics", status="completed")
        return 0
    except Exception as e:
        logger.error(f"Generate full metrics failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
