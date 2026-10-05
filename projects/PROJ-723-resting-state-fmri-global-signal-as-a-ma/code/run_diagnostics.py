import os
import sys
import logging
from pathlib import Path

# Ensure the code directory is in the path
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from config import ensure_directories
from diagnostics import main
from utils import get_logger

logger = get_logger(__name__)

def main_entry():
    """
    Wrapper entry point for running diagnostics.
    Ensures directories exist and logs start time.
    """
    logger.info("Starting Diagnostics Pipeline (T024) via run_diagnostics.py")
    
    # Ensure required directories exist
    ensure_directories(["data/results"])
    
    # Run the main diagnostics function
    exit_code = main()
    
    if exit_code == 0:
        logger.info("Diagnostics pipeline completed successfully.")
    else:
        logger.error("Diagnostics pipeline failed.")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main_entry())