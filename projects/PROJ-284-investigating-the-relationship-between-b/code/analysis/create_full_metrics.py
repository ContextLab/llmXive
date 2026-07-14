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
    Runner script specifically for generating full_metrics.csv.
    Ensures T023b output is written to disk.
    """
    logger.log("create_full_metrics", step="T023b", status="started")
    try:
        metrics_df = load_metrics_data()
        
        # Ensure PCA scores exist (if not, run them)
        factor_scores_path = Path("data/analysis/factor_scores.csv")
        if not factor_scores_path.exists():
            logger.log("create_full_metrics", action="running_pca", reason="scores_missing")
            _, factor_scores_df = run_pca_on_metrics(metrics_df)
        else:
            factor_scores_df = pd.read_csv(factor_scores_path)
        
        # Generate full metrics
        full_df = generate_full_metrics(metrics_df, factor_scores_df)
        
        logger.log("create_full_metrics", step="T023b", status="completed", output="data/analysis/full_metrics.csv")
    except Exception as e:
        logger.log("create_full_metrics", step="T023b", status="failed", error=str(e))
        raise

if __name__ == "__main__":
    main()
