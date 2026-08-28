"""
Verification logic for compositional descriptors.
Specifically checks for the presence of the 'first_ionization_energy' column
as required by Functional Requirement FR-002.
"""
import logging
import sys
from pathlib import Path
from typing import List, Tuple, Optional

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Path to the processed descriptors file
DESCRIPTORS_PATH = Path("data/processed/descriptors.csv")

# Required column per FR-002
FR_002_REQUIRED_COLUMN = "first_ionization_energy"

def verify_column_presence(df: pd.DataFrame, column_name: str) -> Tuple[bool, Optional[str]]:
    """
    Verify if a specific column exists in the DataFrame.

    Args:
        df: The DataFrame to check.
        column_name: The name of the column to verify.

    Returns:
        Tuple of (is_present, error_message).
        If present, error_message is None.
        If missing, is_present is False and error_message describes the failure.
    """
    if column_name not in df.columns:
        available_cols = ", ".join(df.columns)
        error_msg = (
            f"FR-002 Violation: Column '{column_name}' is missing from the dataset. "
            f"Available columns: [{available_cols}]"
        )
        return False, error_msg
    return True, None

def verify_column_data_validity(df: pd.DataFrame, column_name: str) -> Tuple[bool, Optional[str]]:
    """
    Verify that the column contains valid numeric data and no nulls.

    Args:
        df: The DataFrame to check.
        column_name: The name of the column to verify.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if column_name not in df.columns:
        return False, f"Column '{column_name}' does not exist to check validity."

    series = df[column_name]

    # Check for nulls
    if series.isnull().any():
        null_count = series.isnull().sum()
        error_msg = (
            f"Data Validity Error: Column '{column_name}' contains {null_count} null values. "
            "All entries must have computed values for FR-002 compliance."
        )
        return False, error_msg

    # Check for numeric type (or convertible)
    if not pd.api.types.is_numeric_dtype(series):
        try:
            pd.to_numeric(series)
        except (ValueError, TypeError):
            error_msg = (
                f"Data Validity Error: Column '{column_name}' contains non-numeric values "
                "that cannot be converted to float."
            )
            return False, error_msg

    return True, None

def main() -> int:
    """
    Main entry point for the verification script.
    Loads data/processed/descriptors.csv and verifies FR-002 requirements.
    Exits with code 0 if successful, 1 if verification fails.
    """
    logger.info(f"Starting verification for {FR_002_REQUIRED_COLUMN}...")

    if not DESCRIPTORS_PATH.exists():
        logger.error(f"Required file not found: {DESCRIPTORS_PATH}")
        logger.error("Ensure code/feature_engineering.py has been run to generate descriptors.csv.")
        return 1

    try:
        df = pd.read_csv(DESCRIPTORS_PATH)
        logger.info(f"Loaded {len(df)} entries from {DESCRIPTORS_PATH}")
    except Exception as e:
        logger.error(f"Failed to load {DESCRIPTORS_PATH}: {e}")
        return 1

    # 1. Verify Column Presence
    logger.info(f"Checking for presence of column: '{FR_002_REQUIRED_COLUMN}'")
    is_present, presence_error = verify_column_presence(df, FR_002_REQUIRED_COLUMN)

    if not is_present:
        logger.error(presence_error)
        return 1
    logger.info(f"✓ Column '{FR_002_REQUIRED_COLUMN}' is present.")

    # 2. Verify Data Validity (Non-null, Numeric)
    logger.info(f"Checking data validity for column: '{FR_002_REQUIRED_COLUMN}'")
    is_valid, validity_error = verify_column_data_validity(df, FR_002_REQUIRED_COLUMN)

    if not is_valid:
        logger.error(validity_error)
        return 1
    logger.info(f"✓ Column '{FR_002_REQUIRED_COLUMN}' contains valid numeric data with no nulls.")

    logger.info("FR-002 Verification PASSED: 'first_ionization_energy' column is present and valid.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
