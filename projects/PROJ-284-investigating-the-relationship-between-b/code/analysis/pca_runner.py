import os
import sys
import logging
from pathlib import Path
from code.logging_config import get_logger
from code.analysis.correlations import main as correlations_main

logger = get_logger(__name__)

def main():
    """
    Runner script for PCA and Full Metrics generation (T023a, T023b).
    Ensures data/analysis/factor_scores.csv and data/analysis/full_metrics.csv are written.
    """
    logger.log("pca_runner_start")
    try:
        # Execute the main logic from correlations.py which handles both PCA and Full Metrics
        correlations_main()
        logger.log("pca_runner_success")
    except Exception as e:
        logger.log("pca_runner_error", error=str(e))
        raise

if __name__ == "__main__":
    main()
