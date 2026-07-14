"""
Standalone script to generate full_metrics.csv (T023b).
Ensures the file is written even if the main analysis runner is skipped.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd
from code.logging_config import get_logger
from code.analysis.correlations import load_metrics_data, perform_pca_on_metrics, save_pca_results, generate_full_metrics, save_full_metrics

logger = get_logger(__name__)

def main():
    """
    Generate full_metrics.csv by merging raw metrics with PCA scores.
    """
    logger.log("create_full_metrics_start")
    try:
        # 1. Load Metrics
        metrics_df = load_metrics_data()
        logger.log("metrics_loaded", shape=metrics_df.shape)

        if metrics_df.empty:
            logger.log("no_metrics_data", action="skipping")
            return 0

        # 2. Perform PCA
        loadings, scores, pca_model = perform_pca_on_metrics(metrics_df)
        
        # Construct scores DataFrame
        scores_df = pd.DataFrame(
            scores, 
            columns=[f"pca_factor_{i+1}" for i in range(scores.shape[1])]
        )
        if "subject_id" in metrics_df.columns:
            scores_df["subject_id"] = metrics_df["subject_id"].values

        # 3. Save PCA Results (Side effect, required by T023a)
        save_pca_results(pca_model, scores, metrics_df)
        logger.log("pca_saved")

        # 4. Generate Full Metrics (T023b Core Logic)
        full_df = generate_full_metrics(metrics_df, scores_df)
        
        # 5. Save Full Metrics
        save_full_metrics(full_df)
        logger.log("full_metrics_created", path="data/analysis/full_metrics.csv")

        return 0
    except Exception as e:
        logger.log("create_full_metrics_error", error=str(e))
        raise

if __name__ == "__main__":
    sys.exit(main())
