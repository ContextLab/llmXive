"""
Script to run T020: Permutation-based multiple-comparison correction.
Entry point for the Westfall-Young max-T procedure.
"""
import os
import sys
import logging
from pathlib import Path
from src.models.metrics import main
from src.utils import setup_logging

def main_wrapper():
    """Wrapper for script execution with logging setup."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Running T020: Permutation-based multiple-comparison correction")
        result = main()
        if result is not None:
            logger.info(f"Successfully processed {len(result)} dimensions")
        return 0
    except Exception as e:
        logger.error(f"Permutation test failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main_wrapper())
