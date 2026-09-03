"""
Runner script for T003: Checksum ERA5 Sample File.
Computes SHA-256 of data/raw/era5_sample.h5 and updates the project state YAML.
"""
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from compute_checksum import main as compute_checksum_main
from setup_logging import setup_logging, get_data_quality_logger

def main():
    """Entry point for the checksum computation of the ERA5 sample file."""
    # Setup logging
    logger = setup_logging()
    data_logger = get_data_quality_logger()

    logger.info("Starting T003: Checksum ERA5 Sample File")
    data_logger.info("Starting T003: Checksum ERA5 Sample File")

    try:
        # The compute_checksum module handles the specific file path logic
        # based on the task definition (data/raw/era5_sample.h5)
        # We invoke the main function which computes the hash and updates state.
        compute_checksum_main()
        
        logger.info("T003 completed successfully: Checksum recorded in state file.")
        data_logger.info("T003 completed successfully: Checksum recorded in state file.")
        return 0
    except Exception as e:
        logger.error(f"T003 failed: {e}")
        data_logger.error(f"T003 failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
