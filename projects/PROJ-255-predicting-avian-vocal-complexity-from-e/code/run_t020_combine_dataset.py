import os
import sys
import logging
from pathlib import Path

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.preprocessing import main
from src.utils.logging import setup_logger

def main_wrapper():
    logger = setup_logger(__name__)
    logger.info("Running T020: Combine filtered data and metrics into final dataset.")
    exit_code = main()
    if exit_code == 0:
        logger.info("T020 completed successfully.")
    else:
        logger.error("T020 failed with exit code %d", exit_code)
    return exit_code

if __name__ == "__main__":
    sys.exit(main_wrapper())