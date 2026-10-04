import sys
import logging
from pathlib import Path
from setup_logging import setup_logging, get_data_quality_logger
from derive_dilemma_complexity import main

def main_entry() -> None:
    setup_logging(log_file="results/logs/processing_log.txt")
    logger = get_data_quality_logger()
    logger.info("Running T028c: Derive Dilemma Complexity")
    try:
        main()
    except Exception as e:
        logger.error(f"T028c failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main_entry()
