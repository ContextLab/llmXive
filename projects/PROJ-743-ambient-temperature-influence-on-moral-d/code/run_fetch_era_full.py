import sys
import logging
from pathlib import Path

# Add project root to path if not already present
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from setup_logging import setup_logging, get_data_quality_logger
from fetch_era_full import main as fetch_main

def main():
    """
    Entry point for executing the full ERA5 fetch script (T002c).
    Runs the fetch logic defined in fetch_era_full.py and ensures
    logging is properly configured.
    """
    setup_logging()
    logger = get_data_quality_logger()
    
    logger.info("Starting T002c: Execute Fetch of full ERA5 dataset.")
    
    try:
        fetch_main()
        logger.info("T002c: Fetch completed successfully.")
    except Exception as e:
        logger.error(f"T002c: Fetch failed with error: {e}")
        raise

if __name__ == "__main__":
    main()
