import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.dropped_records_aggregator import main
from src.utils.logging import setup_logger

def main_wrapper():
    """
    Wrapper for T021 aggregation script.
    
    This script aggregates all dropped records from the data filtering pipeline
    into a single file for audit trail purposes.
    """
    # Setup logger
    logger = setup_logger("T021_Aggregation")
    logger.info("Starting T021: Dropped Records Aggregation")
    
    try:
        result = main()
        logger.info(f"Successfully aggregated dropped records to: {result}")
        return 0
    except Exception as e:
        logger.error(f"Error during T021 aggregation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main_wrapper())