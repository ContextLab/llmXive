import sys
import logging
from pathlib import Path
from setup_logging import setup_logging, get_data_quality_logger
from derive_demographics import main

def main_entry():
    setup_logging()
    logger = get_data_quality_logger()
    logger.info("Starting demographic covariate derivation (T028a)...")
    try:
        main()
        logger.info("Demographic covariate derivation completed successfully.")
    except Exception as e:
        logger.error(f"Demographic covariate derivation failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main_entry()
