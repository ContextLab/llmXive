"""
Verification script for T014b: Confirm 'first ionization energy' column presence.

This script verifies that the 'data/processed/descriptors.csv' file contains the
'first_ionization_energy' column as required by FR-002, and that the column
contains valid non-null numeric data.
"""

import logging
import sys
from pathlib import Path

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
DESCRIPTORS_PATH = Path("data/processed/descriptors.csv")
REQUIRED_COLUMN = "first_ionization_energy"
FR_002_REFERENCE = "FR-002"

def verify_column_presence(df: pd.DataFrame, column_name: str) -> bool:
    """Check if the specified column exists in the DataFrame."""
    return column_name in df.columns

def verify_column_data_validity(df: pd.DataFrame, column_name: str) -> tuple[bool, int, int]:
    """
    Check if the column contains valid numeric data.
    Returns: (is_valid, non_null_count, total_count)
    """
    if column_name not in df.columns:
        return False, 0, len(df)

    series = df[column_name]
    non_null_count = series.notna().sum()
    total_count = len(df)

    # Check if all non-null values are numeric
    try:
        pd.to_numeric(series.dropna(), errors='raise')
        is_valid = True
    except (ValueError, TypeError):
        is_valid = False

    return is_valid, non_null_count, total_count

def main() -> int:
    """
    Main verification routine.
    Returns 0 on success, 1 on failure.
    """
    logger.info(f"Starting verification for {FR_002_REFERENCE}: {REQUIRED_COLUMN}")

    # Check if file exists
    if not DESCRIPTORS_PATH.exists():
        logger.error(f"Desired file not found: {DESCRIPTORS_PATH}")
        logger.error("Ensure T014 (feature_engineering.py) has been run successfully.")
        return 1

    try:
        df = pd.read_csv(DESCRIPTORS_PATH)
        logger.info(f"Loaded descriptors from {DESCRIPTORS_PATH} ({len(df)} rows)")
    except Exception as e:
        logger.error(f"Failed to read {DESCRIPTORS_PATH}: {e}")
        return 1

    # Verify column presence
    if not verify_column_presence(df, REQUIRED_COLUMN):
        logger.error(f"REQUIRED COLUMN MISSING: '{REQUIRED_COLUMN}' not found in {DESCRIPTORS_PATH}")
        logger.error(f"Available columns: {list(df.columns)}")
        logger.error(f"Verification FAILED for {FR_002_REFERENCE}")
        return 1

    logger.info(f"Column '{REQUIRED_COLUMN}' is present.")

    # Verify data validity
    is_valid, non_null, total = verify_column_data_validity(df, REQUIRED_COLUMN)

    if not is_valid:
        logger.error(f"Column '{REQUIRED_COLUMN}' contains invalid non-numeric data.")
        logger.error(f"Verification FAILED for {FR_002_REFERENCE}")
        return 1

    if non_null == 0:
        logger.error(f"Column '{REQUIRED_COLUMN}' contains only null values.")
        logger.error(f"Verification FAILED for {FR_002_REFERENCE}")
        return 1

    logger.info(f"Data validation PASSED: {non_null}/{total} non-null values found.")
    logger.info(f"Verification SUCCESSFUL for {FR_002_REFERENCE}")
    logger.info(f"Output file: {DESCRIPTORS_PATH}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
