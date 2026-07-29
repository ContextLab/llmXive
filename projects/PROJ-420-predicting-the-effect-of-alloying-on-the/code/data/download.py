import sys
import logging
from pathlib import Path
from data_extraction import run_extraction as extraction_main
from logging_config import setup_logging, get_logger
from config import get_config

def main():
    """CLI wrapper for data extraction (T016)."""
    setup_logging()
    logger = get_logger(__name__)
    
    try:
        logger.info("Starting data extraction pipeline (T016)")
        config = get_config()
        
        # Ensure directories exist
        Path(config.data_raw_dir).mkdir(parents=True, exist_ok=True)
        
        # Run extraction
        extraction_main()
        
        logger.info("Data extraction pipeline finished successfully.")
        
    except Exception as e:
        logger.error(f"Data extraction failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
