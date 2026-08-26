import os
import sys
import logging
from pathlib import Path
from src.cli.run_pipeline import main as batch_processing_main
from src.utils import setup_logging

def main():
    """
    Wrapper script to run the US2 batch processing task.
    """
    logger = setup_logging()
    logger.info("Starting US2 Batch Processing (T022)...")
    
    try:
        batch_processing_main()
        logger.info("US2 Batch Processing completed successfully.")
    except SystemExit as e:
        if e.code != 0:
            logger.error("Batch processing failed with exit code %d", e.code)
            sys.exit(e.code)
        else:
            sys.exit(0)
    except Exception as e:
        logger.exception("Unhandled exception in batch processing")
        sys.exit(1)

if __name__ == "__main__":
    main()