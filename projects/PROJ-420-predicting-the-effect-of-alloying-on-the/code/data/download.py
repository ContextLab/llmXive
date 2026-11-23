import sys
import logging
from pathlib import Path
from data_extraction import run_extraction as extraction_main
from logging_config import setup_logging, get_logger
from config import get_config

def main():
    """CLI wrapper for data extraction."""
    setup_logging()
    logger = get_logger(__name__)
    
    try:
        config = get_config()
        output_path = Path(config.data_raw_dir) / "openml_aluminum.json"
        
        logger.info("Starting data extraction pipeline (T016)")
        logger.info(f"Output path: {output_path}")
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        success = extraction_main(output_path)
        
        if not success:
            logger.error("Data extraction failed.")
            sys.exit(1)
            
        logger.info("Data extraction completed successfully.")
        
    except Exception as e:
        logger.error(f"Data extraction failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
