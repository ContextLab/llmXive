"""Standalone runner for PCA analysis on network metrics."""
import sys
import logging
from pathlib import Path
from logging_config import get_logger
from analysis.correlations import main as pca_main

logger = get_logger(__name__)


def main():
    """Execute PCA analysis pipeline."""
    metrics_file = "data/analysis/network_metrics.csv"
    
    if not Path(metrics_file).exists():
        logger.log("error", message=f"Input metrics file not found: {metrics_file}")
        sys.exit(1)
    
    try:
        pca_main(metrics_file)
        logger.log("pca_runner_success")
    except Exception as e:
        logger.log("pca_runner_error", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
