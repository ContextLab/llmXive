"""
Validation script for simulation metrics.

Scans all parquet files in data/raw/ for NaN values.
Exits with code 1 if any NaN values are found, code 0 otherwise.
"""
import os
import sys
import glob
import logging
import pandas as pd
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def scan_parquet_for_nans(file_path: str) -> bool:
    """
    Scan a single parquet file for NaN values.

    Args:
        file_path: Path to the parquet file

    Returns:
        True if NaN values are found, False otherwise
    """
    try:
        logger.info(f"Scanning {file_path} for NaN values...")
        df = pd.read_parquet(file_path)

        nan_count = df.isna().sum().sum()

        if nan_count > 0:
            logger.error(f"Found {nan_count} NaN values in {file_path}")
            # Log which columns have NaNs
            nan_columns = df.columns[df.isna().any()].tolist()
            logger.error(f"Columns with NaN values: {nan_columns}")
            return True
        else:
            logger.info(f"No NaN values found in {file_path}")
            return False

    except Exception as e:
        logger.error(f"Error scanning {file_path}: {e}")
        raise

def validate_metrics_directory(raw_data_dir: str) -> bool:
    """
    Validate all parquet files in the raw data directory.

    Args:
        raw_data_dir: Path to the directory containing parquet files

    Returns:
        True if any NaN values are found across all files, False otherwise
    """
    raw_path = Path(raw_data_dir)

    if not raw_path.exists():
        logger.warning(f"Directory {raw_data_dir} does not exist. No files to validate.")
        return False

    parquet_files = list(raw_path.glob("*.parquet"))

    if not parquet_files:
        logger.warning(f"No parquet files found in {raw_data_dir}")
        return False

    logger.info(f"Found {len(parquet_files)} parquet files to validate")

    nan_found = False
    for file_path in parquet_files:
        try:
            if scan_parquet_for_nans(str(file_path)):
                nan_found = True
        except Exception as e:
            logger.error(f"Failed to validate {file_path}: {e}")
            nan_found = True

    return nan_found

def main():
    """Main entry point for the validation script."""
    # Default to data/raw relative to project root
    # Allow override via environment variable or command line
    raw_data_dir = os.environ.get("RAW_DATA_DIR", "data/raw")

    if len(sys.argv) > 1:
        raw_data_dir = sys.argv[1]

    logger.info(f"Validating metrics in {raw_data_dir}")

    nan_found = validate_metrics_directory(raw_data_dir)

    if nan_found:
        logger.error("VALIDATION FAILED: NaN values detected in one or more parquet files")
        sys.exit(1)
    else:
        logger.info("VALIDATION PASSED: No NaN values detected")
        sys.exit(0)

if __name__ == "__main__":
    main()