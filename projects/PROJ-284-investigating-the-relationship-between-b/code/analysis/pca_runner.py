"""
Runner script for PCA analysis.
This script executes the PCA analysis and saves results.
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
    Main entry point for PCA runner.
    """
    logger.log("pca_runner", step="start")
    
    try:
        # Run the correlation analysis which includes PCA
        correlations_main()
        logger.log("pca_runner", step="complete", status="success")
    except Exception as e:
        logger.log("pca_runner", step="failed", error=str(e))
        raise

if __name__ == "__main__":
    main()
