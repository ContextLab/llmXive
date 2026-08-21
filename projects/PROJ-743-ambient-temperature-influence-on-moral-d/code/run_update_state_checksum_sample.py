import sys
import logging
from pathlib import Path

from update_state_checksum_sample import main
from setup_logging import setup_logging, get_data_quality_logger

def main_entry():
    """
    Entry point script to run the T003 checksum update for the ERA5 sample file.
    This script sets up logging and calls the main function from update_state_checksum_sample.
    """
    logger = setup_logging()
    logger.info("Executing run_update_state_checksum_sample.py (T003)")

    try:
        main()
        logger.info("T003 execution completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"T003 execution failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main_entry())