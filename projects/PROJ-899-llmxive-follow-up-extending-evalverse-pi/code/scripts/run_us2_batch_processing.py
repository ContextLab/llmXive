import os
import sys
import logging
from pathlib import Path
from src.cli.run_pipeline import main as batch_processing_main
from src.utils import setup_logging

def main():
    """
    Wrapper script to execute the batch processing pipeline (T022a).
    Ensures proper logging setup and error handling.
    """
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Executing batch processing pipeline (T022a)...")
        batch_processing_main()
        logger.info("Batch processing completed successfully.")
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
