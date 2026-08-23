import sys
import logging
from pathlib import Path
from update_state_checksum_sample import main
from setup_logging import setup_logging, get_data_quality_logger

def main_entry():
    """
    Entry point for running T003 checksum sample update.
    """
    setup_logging()
    logger = get_data_quality_logger()
    logger.info("Executing T003: Checksum Sample update.")
    try:
        main()
    except SystemExit as e:
        if e.code != 0:
            logger.error("T003 execution failed.")
            sys.exit(e.code)
        logger.info("T003 execution completed successfully.")

if __name__ == "__main__":
    main_entry()