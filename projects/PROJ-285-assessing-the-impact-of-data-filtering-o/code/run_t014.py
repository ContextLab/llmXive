"""
Runner script for Task T014: Generate Detection Matrix.
This script executes the filtering logic and writes the output to data/processed/detection_matrix.csv.
"""
import sys
import os
import logging
from pathlib import Path

# Add the code directory to the path to allow relative imports
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.logging_config import configure_logging, get_logger
from src.filter import main as run_filter_main

def main():
    configure_logging()
    logger = get_logger(__name__)
    
    logger.info("Starting T014 execution via run_t014.py")
    
    try:
        run_filter_main()
        logger.info("T014 execution completed successfully.")
    except Exception as e:
        logger.critical(f"T014 execution failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()