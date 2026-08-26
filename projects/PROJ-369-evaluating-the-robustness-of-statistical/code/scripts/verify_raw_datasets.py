"""
Run-book script for T055: Verify Raw Datasets.

This script acts as the synchronization barrier between T014 (Download)
and T015 (Preprocessing). It ensures all required raw datasets are present
and valid before any preprocessing begins.

Usage:
    python code/scripts/verify_raw_datasets.py
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.validator import main as validator_main
from src.utils.logging import setup_logger


def main() -> int:
    """
    Entry point for the verify_raw_datasets script.

    Sets up logging and calls the validator main function.

    Returns:
        0 if validation passes, 1 if validation fails.
    """
    # Set up logging
    log_path = project_root / "logs" / "verify_raw_datasets.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = setup_logger(
        name="verify_raw_datasets",
        log_file=str(log_path),
        level=logging.INFO
    )

    logger.info("Executing verify_raw_datasets script (T055)...")

    try:
        result_code = validator_main()
        if result_code == 0:
            logger.info("Raw dataset verification completed successfully.")
        else:
            logger.error("Raw dataset verification failed.")
        return result_code
    except Exception as e:
        logger.critical(f"Unexpected error in verify_raw_datasets: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
