"""
Runner script for T004 to ensure it is invoked by the run-book.
"""
import sys
import logging
from pathlib import Path
from setup_logging import setup_logging, get_data_quality_logger
from validate_era5_sample_integrity import main

def main_entry():
    # Setup logging infrastructure
    setup_logging()
    logger = get_data_quality_logger()
    logger.info("Executing T004: Validate ERA5 Sample Integrity")
    
    try:
        exit_code = main()
        if exit_code == 0:
            logger.info("T004 completed successfully.")
        else:
            logger.error("T004 failed.")
        sys.exit(exit_code)
    except Exception as e:
        logger.critical(f"T004 execution failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main_entry()