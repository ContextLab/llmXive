import logging
import sys
from pathlib import Path
from src.preprocessing.preprocess_pipeline import main as run_pipeline
from src.utils.logging_config import setup_logging

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting preprocessing pipeline script...")
    
    exit_code = run_pipeline()
    
    if exit_code == 0:
        logger.info("Preprocessing pipeline completed successfully.")
    else:
        logger.error("Preprocessing pipeline failed.")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
