"""
Script to run the manual curator pipeline.
Invoked by quickstart.md to ensure data/raw/manual_curated.csv is produced.
"""
import logging
import sys
from pathlib import Path
from src.ingestion.manual_curator import main as run_pipeline
from src.utils.logging_config import setup_logging

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Manual Curator Pipeline...")
    
    try:
        run_pipeline()
        logger.info("Manual Curator Pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Manual Curator Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()