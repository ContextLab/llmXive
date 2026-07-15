"""
Script to run the T015 preprocessing pipeline.
This script is added to the quickstart run-book to ensure data/processed/filtered.csv is generated.
"""
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import configure_root_logger
from data.preprocessing import run_preprocessing_pipeline

def main():
    configure_root_logger()
    logger = logging.getLogger(__name__)
    
    logger.info("Running T015 Preprocessing Pipeline...")
    
    try:
        df = run_preprocessing_pipeline()
        logger.info(f"Success. Processed {len(df)} rows.")
        logger.info(f"Output written to data/processed/filtered.csv")
        return 0
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
