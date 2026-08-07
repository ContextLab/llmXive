"""
Script to run the preprocessing pipeline.
This script is invoked by the quickstart run-book to generate data/processed/alloys_raw.csv.
"""
import logging
import sys
from pathlib import Path
from src.preprocessing.preprocess_pipeline import main as run_pipeline
from src.utils.logging_config import setup_logging

def main():
    """Main entry point for the preprocessing script."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Executing Preprocessing Pipeline via script wrapper...")
        run_pipeline()
        logger.info("Preprocessing script completed successfully.")
    except Exception as e:
        logger.error(f"Preprocessing script failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
