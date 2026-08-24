"""
Verify the existence and content of the ventral striatum activation CSV file.

Task T016d: Verify `data/processed/ventral_striatum_activation.csv` exists
and contains the required columns (subject_id, mean_activation).
"""

import os
import sys
import csv
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define the expected file path relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "ventral_striatum_activation.csv"
REQUIRED_COLUMNS = {"subject_id", "mean_activation"}


def verify_file_exists(path: Path) -> bool:
    """Check if the file exists."""
    if not path.exists():
        logger.error(f"File not found: {path}")
        return False
    if path.stat().st_size == 0:
        logger.error(f"File is empty: {path}")
        return False
    return True


def verify_columns(path: Path) -> bool:
    """Check if the file contains the required columns."""
    try:
        with open(path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                logger.error("CSV file has no header row.")
                return False

            actual_columns = set(reader.fieldnames)
            missing_columns = REQUIRED_COLUMNS - actual_columns

            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                logger.error(f"Found columns: {actual_columns}")
                return False

            logger.info(f"All required columns present: {REQUIRED_COLUMNS}")
            return True

    except csv.Error as e:
        logger.error(f"CSV parsing error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error reading file: {e}")
        return False


def main():
    """Main entry point for verification."""
    logger.info(f"Verifying file: {OUTPUT_PATH}")

    if not verify_file_exists(OUTPUT_PATH):
        logger.error("Verification FAILED: File missing or empty.")
        sys.exit(1)

    if not verify_columns(OUTPUT_PATH):
        logger.error("Verification FAILED: Missing required columns.")
        sys.exit(1)

    logger.info("Verification PASSED: File exists and contains required columns.")
    sys.exit(0)


if __name__ == "__main__":
    main()