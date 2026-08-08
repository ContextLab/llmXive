"""
T041: Verify presence of data/raw/real_ratings.csv before downstream analysis.

This script acts as a guard clause for the pipeline. It ensures that the
real ratings dataset exists at the expected location before any downstream
analysis (LMM, sensitivity analysis) attempts to run.

If the file is missing, the script exits with a non-zero status code and
a clear error message, preventing silent failures or downstream processing
of empty/missing data.

Verification: Script exits with error if missing.
"""
import sys
import os
from pathlib import Path

# Import project configuration to ensure path consistency
from config import get_raw_data_dir

# Import logging infrastructure
from logging_config import setup_logging, get_logger

# Initialize logger
setup_logging()
logger = get_logger(__name__)

# Define the expected file path relative to project root
EXPECTED_FILENAME = "real_ratings.csv"

def verify_real_ratings_presence() -> bool:
    """
    Checks if data/raw/real_ratings.csv exists.

    Returns:
        bool: True if file exists, False otherwise.
    """
    data_dir = get_raw_data_dir()
    file_path = data_dir / EXPECTED_FILENAME

    if not data_dir.exists():
        logger.error(f"Raw data directory does not exist: {data_dir}")
        return False

    if not file_path.exists():
        logger.error(f"Required file missing: {file_path}")
        logger.error("Downstream analysis cannot proceed without real ratings data.")
        return False

    # Check file size to ensure it's not empty (basic sanity check)
    if file_path.stat().st_size == 0:
        logger.error(f"File exists but is empty: {file_path}")
        return False

    logger.info(f"Verification passed: {file_path} exists and is non-empty.")
    return True

def main():
    """
    Main entry point for T041 verification script.

    Exits with code 0 if verification passes, 1 if it fails.
    """
    logger.info("Starting T041: Verify presence of real_ratings.csv")

    is_present = verify_real_ratings_presence()

    if not is_present:
        logger.error("T041 FAILED: Real ratings file missing.")
        sys.exit(1)

    logger.info("T041 PASSED: Real ratings file verified.")
    sys.exit(0)

if __name__ == "__main__":
    main()