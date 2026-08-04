import os
import sys
import logging
from pathlib import Path

# Add project root to path if necessary (though typically handled by environment)
# Assuming the script is run from the project root or code/ directory
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.dropped_records_aggregator import main
from src.utils.logging import setup_logger

def main_wrapper():
    """
    Wrapper for T021 execution to ensure logging is configured.
    """
    logger = setup_logger("T021_Aggregation")
    logger.info("Starting T021: Dropped Records Aggregation")
    
    try:
        count = main()
        logger.info(f"T021 Execution Successful. Dropped records count: {count}")
        return 0
    except Exception as e:
        logger.error(f"T021 Execution Failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main_wrapper())
