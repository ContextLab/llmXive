"""
Script to calculate convex hull distances for all entries in the dataset.
This script implements T037.
"""
import logging
from pathlib import Path
import sys

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.hull_distance import main
from utils.logging import setup_logger

def main_script():
    logger = setup_logger(__name__)
    logger.info("Running hull distance calculation script.")
    try:
        result = main()
        if result is not None:
            logger.info(f"Successfully calculated hull distances for {len(result)} entries.")
        else:
            logger.warning("No results returned. Check logs for errors.")
    except Exception as e:
        logger.error(f"Script failed with error: {e}")
        raise

if __name__ == "__main__":
    main_script()
