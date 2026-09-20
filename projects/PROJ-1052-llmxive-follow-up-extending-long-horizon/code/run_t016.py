"""
Runner script for Task T016: Add logic to exclude "unrecoverable errors" (baseline failures)
from recovery success metric calculation but log them separately.

This script executes the metric calculation logic defined in code/utils/metrics.py.
"""
import sys
import os
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.metrics import main as t016_main

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(project_root / 'logs' / 't016_run.log')
        ]
    )

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting T016: Recovery Metrics Calculation")
    
    try:
        t016_main()
        logger.info("T016 completed successfully.")
    except Exception as e:
        logger.error(f"T016 failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
