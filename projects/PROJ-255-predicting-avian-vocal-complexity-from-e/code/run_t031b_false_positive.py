import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.analysis.false_positive import main
from src.utils.logging import setup_logger

def main_wrapper():
    """
    Wrapper for the false positive analysis script.
    Ensures logging is set up and calls the main function.
    """
    setup_logger()
    logger = logging.getLogger(__name__)
    logger.info("Running T031b: False Positive Analysis")
    
    try:
        main()
        logger.info("T031b completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"T031b failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main_wrapper())
