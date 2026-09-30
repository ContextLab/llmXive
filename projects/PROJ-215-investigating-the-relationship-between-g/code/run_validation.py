"""
Runner script for T032a: Validation on Independent Cohort.
This script orchestrates the validation process.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path if needed
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.validation import main
from code.utils.logging import get_logger

logger = get_logger(__name__)

def main_entry():
    """
    Main entry point for the validation runner.
    """
    logger.info("Starting Validation Runner (T032a)")
    try:
        main()
        logger.info("Validation completed successfully.")
    except Exception as e:
        logger.error(f"Validation runner failed: {e}")
        # Re-raise to ensure the pipeline knows it failed
        raise

if __name__ == '__main__':
    main_entry()
