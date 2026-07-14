"""
Runner script for PCA and Full Metrics generation (T023a, T023b).
This script is invoked by the quickstart run-book to ensure deliverables are produced.
"""
import os
import sys
import logging
from pathlib import Path
from code.analysis.correlations import main as correlations_main
from code.logging_config import get_logger

logger = get_logger(__name__)

def main():
    """
    Entrypoint for the PCA and Full Metrics pipeline.
    Calls the main logic in correlations.py.
    """
    logger.log("pca_runner_start")
    try:
        # Ensure output directories exist
        Path("data/analysis").mkdir(parents=True, exist_ok=True)
        
        # Run the full analysis logic (PCA + Full Metrics + Correlations)
        # This function handles loading, PCA, merging, and saving.
        result = correlations_main()
        
        if result == 0:
            logger.log("pca_runner_success")
            return 0
        else:
            logger.log("pca_runner_failure")
            return 1
    except Exception as e:
        logger.log("pca_runner_error", error=str(e))
        return 1

if __name__ == "__main__":
    sys.exit(main())
