"""
Dataset Threshold Validator for Context-Bound Filtering.

This module implements the validation logic to ensure the filtered dataset
meets the minimum sample size requirements before expensive execution begins.

Constraints:
- If row count < 50 (exploratory threshold): HARD FAILURE (exit 1)
- If 50 <= rows < 800: Log "Exploratory Mode" (exit 0)
- If rows >= 800: Log "Confirmatory Mode" (exit 0)

Note: The 50-row threshold applies to the *filtered* dataset count.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
import pyarrow.parquet as pq

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Threshold constants
EXPLORATORY_THRESHOLD = 50
CONFIRMATORY_THRESHOLD = 800

def count_rows_in_parquet(file_path: Path) -> int:
    """
    Count the number of rows in a Parquet file.

    Args:
        file_path: Path to the Parquet file.

    Returns:
        Integer count of rows.

    Raises:
        FileNotFoundError: If the file does not exist.
        Exception: If the file cannot be read as Parquet.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Parquet file not found: {file_path}")

    try:
        # Use Parquet metadata to count rows without loading data into memory
        parquet_file = pq.ParquetFile(file_path)
        return parquet_file.metadata.num_rows
    except Exception as e:
        logger.error(f"Failed to read Parquet file {file_path}: {e}")
        raise

def validate_thresholds(row_count: int, file_path: Path) -> bool:
    """
    Validate that the row count meets the required thresholds.

    Logic per T045:
    - If rows < 50: Raise "Insufficient Context-Bound Data" (exit 1).
    - If 50 <= rows < 800: Log "Exploratory Mode" (exit 0).
    - If rows >= 800: Log "Confirmatory Mode" (exit 0).

    Args:
        row_count: Number of rows in the dataset.
        file_path: Path to the dataset (for error messaging).

    Returns:
        True if thresholds are met, False otherwise.

    Raises:
        SystemExit: If thresholds are not met (hard failure).
    """
    logger.info(f"Validating row count for {file_path}")
    logger.info(f"Row count: {row_count}")

    if row_count < EXPLORATORY_THRESHOLD:
        error_msg = (
            f"Insufficient Context-Bound Data: "
            f"Row count ({row_count}) is below exploratory threshold ({EXPLORATORY_THRESHOLD})."
        )
        logger.error(error_msg)
        # Exit 1 for hard failure
        raise SystemExit(1)

    if row_count < CONFIRMATORY_THRESHOLD:
        logger.info("Exploratory Mode: Row count is between 50 and 799.")
        # Exit 0 for success (exploratory mode is allowed)
        return True

    logger.info("Confirmatory Mode: Row count is >= 800.")
    # Exit 0 for success
    return True

def main():
    """
    Main entry point for the threshold validator script.

    Usage:
        python code/analysis/threshold_validator.py --input data/filtered_swe_bench_v1.parquet
    """
    parser = argparse.ArgumentParser(
        description="Validate datasets row count against thresholds."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the filtered Parquet dataset file."
    )

    args = parser.parse_args()

    input_path = Path(args.input)

    logger.info(f"Starting threshold validation for: {input_path}")

    try:
        row_count = count_rows_in_parquet(input_path)
        validate_thresholds(row_count, input_path)
        logger.info("Validation successful. Dataset meets requirements.")
        sys.exit(0)

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except SystemExit as e:
        # Re-raise SystemExit to ensure correct exit code is propagated
        raise
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()