import os
import sys
import logging
from pathlib import Path
from src.models.evaluate import main as evaluate_main
from src.utils import setup_logging

def main():
    """Entry point for running baseline comparisons script."""
    logger = setup_logging("run_baseline_comparisons", level=logging.INFO)
    try:
        evaluate_main()
        logger.info("Baseline comparisons completed successfully.")
    except Exception as e:
        logger.error(f"Baseline comparisons failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()