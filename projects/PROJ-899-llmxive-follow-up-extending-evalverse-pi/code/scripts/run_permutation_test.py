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
    """
    Wrapper script for T020: Permutation-based multiple-comparison correction.
    """
    # Setup logging
    logger = setup_logging("run_permutation_test")
    logger.info("Starting permutation test (T020)")

    try:
        result = main()
        if result == 0:
            logger.info("Permutation test completed successfully")
        else:
            logger.error("Permutation test failed")
        return result
    except Exception as e:
        logger.exception(f"Permutation test failed with exception: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main_wrapper())
