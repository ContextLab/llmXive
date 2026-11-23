import sys
import logging
from pathlib import Path
from update_state_checksum_sample import main
from setup_logging import setup_logging, get_data_quality_logger

def main_entry():
    """
    Entry point for the checksum update script for the ERA5 sample file.
    This script computes the SHA-256 checksum of data/raw/era5_sample.h5
    and updates the project state file.
    """
    logger = setup_logging()
    logger.info("Starting checksum update for ERA5 sample file.")
    
    try:
        main()
        logger.info("Checksum update completed successfully.")
    except Exception as e:
        logger.error(f"Checksum update failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main_entry()
