"""
Script to run the correlation calculation pipeline (T016a, T016b, T016c, T020a).
"""
import os
import sys
import logging
from pathlib import Path

from src.models.metrics import main
from src.utils import setup_logging

def main_wrapper():
    """
    Wrapper function to execute the correlation calculation.
    """
    setup_logging(__name__)
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting correlation calculation pipeline...")
        main()
        logger.info("Correlation calculation completed successfully.")
    except Exception as e:
        logger.error(f"Correlation calculation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main_wrapper()