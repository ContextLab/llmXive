"""
Script to run T020c: FDR Correction.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.metrics import main as metrics_main
from src.utils import setup_logging

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting T020c: FDR Correction")
    
    exit_code = metrics_main()
    
    if exit_code == 0:
        logger.info("T020c completed successfully.")
    else:
        logger.error("T020c failed.")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
