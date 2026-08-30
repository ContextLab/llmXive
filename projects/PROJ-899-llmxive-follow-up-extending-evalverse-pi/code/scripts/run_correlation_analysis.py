"""
Script to run the full correlation analysis pipeline including bootstrapping.
This script is invoked by the run-book to produce data/processed/correlations.csv.
"""
import os
import sys
import logging
from pathlib import Path
from src.models.metrics import main
from src.utils import setup_logging

def main_wrapper():
    """Wrapper to handle logging and exit codes."""
    setup_logging()
    logger = logging.getLogger(__name__)
    try:
        exit_code = main()
        return exit_code
    except Exception as e:
        logger.error(f"Correlation analysis script failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main_wrapper())