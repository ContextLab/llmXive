"""
Runner script for PCA analysis (T023a).
"""
import os
import sys
import logging
from pathlib import Path
from code.analysis.correlations import main as correlations_main
from code.logging_config import get_logger

logger = get_logger(__name__)

def main():
    """Entry point for PCA runner."""
    logger.info("Starting PCA analysis runner...")
    try:
        correlations_main()
    except Exception as e:
        logger.error(f"PCA runner failed: {e}")
        sys.exit(1)
    logger.info("PCA runner finished successfully.")

if __name__ == "__main__":
    main()
