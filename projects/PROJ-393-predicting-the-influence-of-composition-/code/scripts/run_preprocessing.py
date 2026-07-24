"""
Script to run the preprocessing pipeline.
This script is invoked by the run-book to generate data/processed/alloys_raw.csv.
"""
import logging
import sys
from pathlib import Path
from src.preprocessing.preprocess_pipeline import main as run_pipeline
from src.utils.logging_config import setup_logging

def main():
    """Entry point for the run-preprocessing script."""
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Executing preprocessing pipeline via run script...")
    
    try:
        run_pipeline()
        logger.info("Preprocessing script finished successfully.")
    except Exception as e:
        logger.error(f"Preprocessing script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
