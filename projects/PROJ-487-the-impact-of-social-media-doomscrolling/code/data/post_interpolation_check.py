import os
import sys
import json
import logging
import pandas as pd
from datetime import datetime

from utils.logging import get_logger

# Constants
COMPLETENESS_THRESHOLD = 0.95  # 95%
INPUT_FILE = "data/processed/aligned_timeseries.csv"
OUTPUT_FILE = "data/processed/completeness_check.json"

logger = get_logger(__name__)

def calculate_completeness(df: pd.DataFrame, date_column: str = "date") -> float:
    """
    Calculate data completeness as (Count of non-null rows) / (Total days in the aligned intersection range).

    Args:
        df: The processed DataFrame.
        date_column: The name of the column containing dates.

    Returns:
        Completeness ratio (0.0 to 1.0).
    """
    if df.empty:
        return 0.0

    # Total days is the count of rows in the aligned intersection
    total_days = len(df)

    if total_days == 0:
        return 0.0

    # Count rows where ALL data columns (excluding the date itself) are non-null
    # We assume the first column is date, and the rest are data series.
    # If there are other metadata columns, they should be excluded or handled specifically.
    # For this task, we check if the row has no NaN values in any column except 'date'.
    data_columns = [col for col in df.columns if col != date_column]

    if not data_columns:
        # If only date column exists, completeness is 1.0 (assuming no empty df)
        return 1.0

    non_null_rows = df[data_columns].dropna(how='any')
    count_non_null = len(non_null_rows)

    completeness = count_non_null / total_days
    return completeness

def check_post_interpolation_completeness(
    input_path: str = INPUT_FILE,
    output_path: str = OUTPUT_FILE,
    threshold: float = COMPLETENESS_THRESHOLD
) -> bool:
    """
    Verifies the processed timeseries file has >= 95% data completeness.

    Args:
        input_path: Path to the aligned_timeseries.csv.
        output_path: Path to save the JSON validation report.
        threshold: Minimum required completeness ratio.

    Returns:
        True if completeness >= threshold, False otherwise.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file is empty or malformed.
    """
    logger.info(f"Checking post-interpolation completeness for {input_path}")

    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        raise

    if df.empty:
        logger.error("Input DataFrame is empty.")
        raise ValueError("Input DataFrame is empty.")

    completeness = calculate_completeness(df)
    logger.info(f"Calculated completeness: {completeness:.4f} ({completeness * 100:.2f}%)")

    # Prepare report
    report = {
        "timestamp": datetime.now().isoformat(),
        "input_file": input_path,
        "total_rows": len(df),
        "non_null_rows": len(df.dropna(subset=[c for c in df.columns if c != "date"], how="any")),
        "completeness_ratio": completeness,
        "threshold": threshold,
        "passed": completeness >= threshold
    }

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Completeness report saved to {output_path}")

    if completeness < threshold:
        logger.error(f"Completeness check FAILED: {completeness:.4f} < {threshold:.4f}")
        return False

    logger.info("Completeness check PASSED.")
    return True

def main():
    """
    Entry point for the post-interpolation completeness check.
    Exits with code 0 on success, 1 on failure.
    """
    try:
        success = check_post_interpolation_completeness()
        if success:
            print("Validation Status: PASSED")
            sys.exit(0)
        else:
            print("Validation Status: FAILED (Completeness < 95%)")
            sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during check: {e}")
        print(f"Error: Unexpected error occurred.")
        sys.exit(1)

if __name__ == "__main__":
    main()