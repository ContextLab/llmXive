"""
Entry point script to execute the full ERA5 dataset fetch (T002c).

This script runs the `fetch_era5_full.py` logic to download the full 2014-2018
ERA5 2m temperature dataset, merge the results, and save to `data/raw/era5_full.h5`.
It also logs the success or failure to `results/logs/data_validation_log.txt`.
"""
import sys
import logging
from pathlib import Path

# Import the main execution function from the implementation module
from fetch_era5_full import main as fetch_main
from setup_logging import setup_logging, get_data_quality_logger

def main():
    """
    Orchestrates the execution of the full ERA5 fetch task.
    """
    # Setup logging infrastructure
    setup_logging()
    logger = get_data_quality_logger()

    logger.info("Starting full ERA5 dataset fetch (Task T002c)...")
    logger.info("Target: data/raw/era5_full.h5")
    logger.info("Period: 2014-01-01 to 2018-12-31")

    try:
        # Execute the fetch logic defined in fetch_era5_full.py
        # This function handles chunking, retry logic, and merging.
        fetch_main()

        logger.info("Full ERA5 dataset fetch completed successfully.")
        logger.info("Output file should be present at: data/raw/era5_full.h5")

    except Exception as e:
        logger.error(f"Full ERA5 dataset fetch FAILED: {e}", exc_info=True)
        # Re-raise to ensure the pipeline fails loudly as per constraints
        raise e

if __name__ == "__main__":
    main()
