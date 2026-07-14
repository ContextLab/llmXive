"""
Runner script for T023a: PCA on network metrics.
Invoked by the main pipeline to generate PCA outputs.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.logging_config import get_logger
from code.analysis.correlations import main as pca_main

logger = get_logger(__name__)

def main():
    logger.log("pca_runner_start")
    try:
        pca_main()
        logger.log("pca_runner_complete")
    except Exception as e:
        logger.log("pca_runner_failed", error=str(e))
        raise

if __name__ == "__main__":
    main()
