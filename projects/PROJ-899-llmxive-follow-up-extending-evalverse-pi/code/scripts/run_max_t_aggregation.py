import os
import sys
import logging
from pathlib import Path
from src.models.metrics import main as metrics_main
from src.utils import setup_logging

def main():
    """
    Wrapper script to execute T020b: Max-T Aggregation.
    """
    setup_logging(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Executing Max-T Aggregation (T020b)...")
    
    try:
        exit_code = metrics_main()
        if exit_code == 0:
            logger.info("Max-T Aggregation finished successfully.")
        else:
            logger.error(f"Max-T Aggregation failed with exit code {exit_code}.")
        return exit_code
    except Exception as e:
        logger.error(f"Critical error in Max-T Aggregation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())