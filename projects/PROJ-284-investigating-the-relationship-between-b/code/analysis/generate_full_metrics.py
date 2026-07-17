"""
Generate Full Metrics script to ensure T023b outputs are generated.
This script merges raw metrics with PCA scores.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.correlations import load_metrics_data, run_pca_on_metrics, generate_full_metrics
from code.logging_config import get_logger

logger = get_logger(__name__)

def main():
    logger.log("start_generate_full_metrics")
    try:
        df = load_metrics_data()
        # Run PCA if not already done (or load existing scores)
        # The run_pca_on_metrics function writes the files, so we can just call it
        # or load the existing files if they exist.
        # For robustness, we call it.
        loadings, scores = run_pca_on_metrics(df)
        generate_full_metrics(df, scores)
        logger.log("generate_full_metrics_success")
    except Exception as e:
        logger.log("generate_full_metrics_failed", error=str(e))
        raise

if __name__ == "__main__":
    main()
