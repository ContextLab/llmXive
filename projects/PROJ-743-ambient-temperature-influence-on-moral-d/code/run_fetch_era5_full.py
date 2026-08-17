import sys
import logging
from pathlib import Path

from fetch_era5_full import main as fetch_main
from setup_logging import setup_logging, get_data_quality_logger

def main():
    """
    Entry point for executing the full ERA5 dataset fetch (Task T002c).
    This script orchestrates the fetch_era5_full.py logic to download
    the 2016-2019 dataset, merge by year, and save to data/raw/era5_full.h5.
    It also logs the execution status to results/logs/data_validation_log.txt.
    """
    logger = setup_logging()
    data_logger = get_data_quality_logger()

    logger.info("Starting execution of T002c: Fetch full ERA5 dataset.")
    try:
        # Execute the fetch logic defined in fetch_era5_full
        fetch_main()
        logger.info("T002c execution completed successfully. File saved to data/raw/era5_full.h5")
        return 0
    except Exception as e:
        logger.error(f"T002c execution failed: {str(e)}")
        data_logger.error(f"Data fetch failed for T002c: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
