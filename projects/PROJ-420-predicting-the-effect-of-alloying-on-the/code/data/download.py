import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_extraction import run_extraction as extraction_main
from logging_config import setup_logging, get_logger
from config import get_config

def main():
    """CLI entry point for data extraction."""
    logger = setup_logging()
    config = get_config()
    
    try:
        logger.info("Starting data extraction...")
        # Run extraction and save raw files
        extraction_main()
        logger.info("Data extraction completed successfully.")
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
