import sys
import logging
from pathlib import Path
from pre_ingestion_validation_gate import main
from setup_logging import setup_logging, get_data_quality_logger

def main_entry() -> None:
    """Entry point for the T006 validation gate runner."""
    setup_logging()
    logger = get_data_quality_logger()
    logger.info("Starting T006 Pre-Ingestion Validation Gate")
    
    try:
        main()
        logger.info("T006 Validation Gate Completed Successfully")
    except Exception as e:
        logger.error(f"T006 Validation Gate Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main_entry()
