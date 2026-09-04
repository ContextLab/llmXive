"""
Task T015b: Target Date Range Validation.

Verifies that data/raw/gdelt_events.csv and data/raw/google_trends.csv
explicitly cover the target date range (2020-01-01 to 2023-12-31).

Exits with code 0 if coverage is complete.
Exits with code 1 if coverage is incomplete.
"""
import os
import sys
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path

# Project root relative to this script location
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

# Target date range as per task description
TARGET_START = datetime(2020, 1, 1).date()
TARGET_END = datetime(2023, 12, 31).date()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_file_date_range(file_path: Path, target_start: datetime, target_end: datetime) -> bool:
    """
    Validates that a CSV file covers the target date range.

    Args:
        file_path: Path to the CSV file.
        target_start: Start date of the required range.
        target_end: End date of the required range.

    Returns:
        True if the file covers the range, False otherwise.
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return False

    try:
        # Load the CSV
        df = pd.read_csv(file_path)

        # Identify the date column
        # Assuming standard schema from T007a: 'date' column exists
        date_col = 'date'
        if date_col not in df.columns:
            logger.error(f"Column '{date_col}' not found in {file_path}. Columns: {list(df.columns)}")
            return False

        # Parse dates
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

        # Drop rows where date parsing failed
        valid_dates = df[df[date_col].notna()]

        if valid_dates.empty:
            logger.error(f"No valid dates found in {file_path}")
            return False

        # Get min and max dates
        min_date = valid_dates[date_col].min().date()
        max_date = valid_dates[date_col].max().date()

        logger.info(f"File: {file_path.name}")
        logger.info(f"  Date range found: {min_date} to {max_date}")
        logger.info(f"  Target range:     {target_start} to {target_end}")

        # Check coverage
        covers_start = min_date <= target_start
        covers_end = max_date >= target_end

        if covers_start and covers_end:
            logger.info(f"  Status: COVERAGE COMPLETE")
            return True
        else:
            reasons = []
            if not covers_start:
                reasons.append(f"Missing start (found {min_date}, need <= {target_start})")
            if not covers_end:
                reasons.append(f"Missing end (found {max_date}, need >= {target_end})")
            logger.error(f"  Status: COVERAGE INCOMPLETE - {', '.join(reasons)}")
            return False

    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return False

def main():
    logger.info("Starting Target Date Range Validation (T015b)")

    gdelt_path = DATA_RAW_DIR / "gdelt_events.csv"
    trends_path = DATA_RAW_DIR / "google_trends.csv"

    gdelt_ok = validate_file_date_range(gdelt_path, TARGET_START, TARGET_END)
    trends_ok = validate_file_date_range(trends_path, TARGET_START, TARGET_END)

    if gdelt_ok and trends_ok:
        logger.info("Validation PASSED: Both files cover the target date range.")
        sys.exit(0)
    else:
        logger.error("Validation FAILED: One or more files do not cover the target date range.")
        sys.exit(1)

if __name__ == "__main__":
    main()