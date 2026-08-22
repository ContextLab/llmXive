import os
import sys
import logging
from pathlib import Path
from src.models.metrics import main
from src.utils import setup_logging

def main_wrapper():
    """
    Wrapper script to run the permutation test (T020).
    This script is invoked by the run-book to produce data/permutation_results.csv.
    """
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting T020: Permutation-based multiple-comparison correction")
        result_df = main()
        logger.info("T020 completed successfully")
        return 0
    except Exception as e:
        logger.error(f"T020 failed with error: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main_wrapper())
