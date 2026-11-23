"""
Script to run the baseline validation gate (T029).

This script executes the baseline check on H=0.5 data to verify that the
hypothesis testing pipeline maintains the correct Type I error rate before
proceeding to Hurst analysis.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.utils.logging import setup_logger
from src.synthesis.validation import main as baseline_main

def main():
    """Main entry point for the baseline validation script."""
    logger = setup_logger("baseline_validation")
    logger.info("Starting baseline validation gate (T029)")
    
    try:
        exit_code = baseline_main()
        if exit_code == 0:
            logger.info("Baseline validation gate PASSED")
        else:
            logger.error("Baseline validation gate FAILED - pipeline blocked")
        return exit_code
    except Exception as e:
        logger.error(f"Baseline validation failed with exception: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
