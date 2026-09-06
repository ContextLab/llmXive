"""
Task T015b: Target Date Range Validation

Verifies that data/raw/gdelt_events.csv and data/raw/google_trends.csv
explicitly cover the target date range (2020-01-01 to 2023-12-31).
"""
import os
import sys
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path

# Import logger from utils
try:
    from utils.logging import get_logger
    logger = get_logger(__name__)
except ImportError:
    # Fallback if utils.logging is not available yet
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "raw"
TARGET_START = datetime(2020, 1, 1)
TARGET_END = datetime(2023, 12, 31)

FILES_TO_CHECK = [
    "gdelt_events.csv",
    "google_trends.csv"
]

def validate_file_date_range(file_path: Path) -> bool:
    """
    Validates that a CSV file covers the target date range.
    Returns True if valid, False otherwise.
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return False

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")
        return False

    # Identify date column
    date_col = None
    for col in df.columns:
        if 'date' in col.lower():
            date_col = col
            break

    if not date_col:
        logger.error(f"No 'date' column found in {file_path}. Columns: {list(df.columns)}")
        return False

    # Parse dates
    try:
        df[date_col] = pd.to_datetime(df[date_col])
    except Exception as e:
        logger.error(f"Failed to parse dates in {file_path}: {e}")
        return False

    min_date = df[date_col].min()
    max_date = df[date_col].max()

    logger.info(f"Checking {file_path.name}:")
    logger.info(f"  Date range in file: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")
    logger.info(f"  Target range:       {TARGET_START.strftime('%Y-%m-%d')} to {TARGET_END.strftime('%Y-%m-%d')}")

    if min_date > TARGET_START:
        logger.error(f"  FAIL: File starts after target start date ({min_date} > {TARGET_START})")
        return False

    if max_date < TARGET_END:
        logger.error(f"  FAIL: File ends before target end date ({max_date} < {TARGET_END})")
        return False

    logger.info(f"  PASS: File covers the target date range.")
    return True

def main():
    logger.info("Starting Target Date Range Validation (T015b)...")
    all_valid = True

    for filename in FILES_TO_CHECK:
        file_path = DATA_DIR / filename
        if not validate_file_date_range(file_path):
            all_valid = False

    if all_valid:
        logger.info("SUCCESS: All files cover the target date range (2020-01-01 to 2023-12-31).")
        sys.exit(0)
    else:
        logger.error("FAILURE: One or more files do not cover the target date range.")
        sys.exit(1)

if __name__ == "__main__":
    main()