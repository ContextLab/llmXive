"""
Script to run T019: Baseline comparisons.
This script is invoked by the run-book to generate data/baseline_results.csv.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.evaluate import main as evaluate_main
from src.utils import setup_logging

def main():
    """Entry point for the baseline comparisons script."""
    setup_logging(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Running T019: Baseline comparisons")
    
    try:
        evaluate_main()
        logger.info("Baseline comparisons completed successfully.")
    except SystemExit as e:
        if e.code != 0:
            logger.error("Baseline comparisons failed.")
            sys.exit(e.code)
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()