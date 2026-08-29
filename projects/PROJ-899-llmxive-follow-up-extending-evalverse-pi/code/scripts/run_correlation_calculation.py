import os
import sys
import logging
from pathlib import Path
from src.models.metrics import main
from src.utils import setup_logging

def main_wrapper():
    """
    Wrapper script to execute T016a correlation calculation.
    """
    # Setup logging
    logger = setup_logging(__name__)
    
    logger.info("Starting correlation calculation (T016a)...")
    
    # Run the main function from metrics module
    exit_code = main()
    
    if exit_code == 0:
        logger.info("Correlation calculation completed successfully")
    else:
        logger.error("Correlation calculation failed")
    
    return exit_code

if __name__ == '__main__':
    sys.exit(main_wrapper())
