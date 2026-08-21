import logging
import sys
from pathlib import Path

from src.analysis.verification import main

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def main_entry():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting T022: Sample Size Verification")
    
    exit_code = main()
    
    if exit_code == 0:
        logger.info("Verification completed successfully.")
    else:
        logger.error("Verification failed.")
        
    return exit_code

if __name__ == "__main__":
    sys.exit(main_entry())
