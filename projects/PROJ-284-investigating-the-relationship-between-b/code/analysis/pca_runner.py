"""
PCA Runner script to ensure T023a outputs are generated.
This script is invoked by the run-book to ensure PCA outputs exist.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.correlations import load_metrics_data, run_pca_on_metrics
from code.logging_config import get_logger

logger = get_logger(__name__)

def main():
    logger.log("start_pca_runner")
    try:
        df = load_metrics_data()
        loadings, scores = run_pca_on_metrics(df)
        logger.log("pca_runner_success", loadings_path="data/analysis/pca_loadings.csv", scores_path="data/analysis/factor_scores.csv")
    except Exception as e:
        logger.log("pca_runner_failed", error=str(e))
        raise

if __name__ == "__main__":
    main()
