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
    """
    Entry point for the run_preprocessing script.
    """
    setup_logging(level=logging.INFO)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Preprocessing Pipeline via run_preprocessing.py...")
    
    try:
        run_pipeline()
        logger.info("Preprocessing pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Preprocessing pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
