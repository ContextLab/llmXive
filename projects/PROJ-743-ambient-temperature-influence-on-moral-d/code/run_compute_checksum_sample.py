"""
Runner script for T003: Checksum ERA5 Sample File.
Invokes compute_checksum_sample.py with proper logging setup.
"""
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from compute_checksum_sample import main
from setup_logging import setup_logging, get_data_quality_logger

def main_entry():
    setup_logging()
    logger = get_data_quality_logger()
    logger.info("Starting T003: Checksum ERA5 Sample File")
    try:
        result = main()
        logger.info(f"T003 completed with status code: {result}")
        return result
    except Exception as e:
        logger.error(f"T003 failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main_entry())