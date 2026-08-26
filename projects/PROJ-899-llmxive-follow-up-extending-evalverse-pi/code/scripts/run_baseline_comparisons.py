import os
import sys
import logging
from pathlib import Path
from src.models.evaluate import main as evaluate_main
from src.utils import setup_logging

def main():
    """
    Script to run T019: Baseline Comparisons.
    """
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Running Baseline Comparisons (T019)...")
    
    try:
        evaluate_main()
        logger.info("Baseline comparisons completed.")
    except Exception as e:
        logger.error(f"Error running baseline comparisons: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()