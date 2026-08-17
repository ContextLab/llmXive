"""
Runner script for T028: Derivation of Age/Gender Covariates.
"""
import sys
import logging
from pathlib import Path

# Add parent to path if needed, though typically run from project root
if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

from setup_logging import setup_logging, get_data_quality_logger
from derive_demographics import main

def main_entry():
    setup_logging()
    logger = get_data_quality_logger()
    logger.info("Starting runner for T028: Derivation of Age/Gender Covariates")
    try:
        main()
    except Exception as e:
        logger.error(f"Runner failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main_entry()
