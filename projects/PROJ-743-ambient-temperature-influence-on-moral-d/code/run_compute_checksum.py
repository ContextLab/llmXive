"""
Runner script to execute the checksum computation for the ERA5 full dataset.

This script is designed to be run as an entry point to compute the SHA-256
checksum of the downloaded ERA5 full dataset and record it in the project
state file.
"""
import sys
import logging
from pathlib import Path

# Add the code directory to the path
code_dir = Path(__file__).parent
sys.path.insert(0, str(code_dir))

from compute_checksum import main
from setup_logging import setup_logging, get_data_quality_logger

def main_entry():
    """
    Main entry point for the checksum computation runner.
    """
    # Setup logging
    setup_logging()
    logger = get_data_quality_logger()

    logger.info("=" * 60)
    logger.info("Starting ERA5 Full Dataset Checksum Computation")
    logger.info("=" * 60)

    try:
        # Run the checksum computation
        exit_code = main()

        if exit_code == 0:
            logger.info("Checksum computation completed successfully")
        else:
            logger.error(f"Checksum computation failed with exit code {exit_code}")

        return exit_code

    except Exception as e:
        logger.error(f"Unexpected error during checksum computation: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main_entry())