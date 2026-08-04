import os
import sys
import logging
import pandas as pd
from pathlib import Path
from code.config import get_data_path, setup_logging

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    "code",
    "loc",
    "cyclomatic_complexity",
    "static_smell_labels"
]

def validate_baseline(output_path: str = None, threshold: float = 0.95) -> bool:
    """
    Validates that the static baseline CSV contains at least `threshold` (default 95%)
    of the sampled functions with all required columns populated.

    Args:
        output_path: Path to the CSV file. Defaults to data/static_baseline.csv.
        threshold: Minimum fraction of rows that must be valid (0.0 to 1.0).

    Returns:
        bool: True if validation passes, False otherwise.

    Raises:
        FileNotFoundError: If the output file does not exist.
        ValueError: If the file is empty or structure is invalid.
    """
    if output_path is None:
        data_dir = get_data_path()
        output_path = os.path.join(data_dir, "static_baseline.csv")

    logger.info(f"Validating baseline at: {output_path}")

    if not os.path.exists(output_path):
        logger.error(f"File not found: {output_path}")
        raise FileNotFoundError(f"Baseline file not found: {output_path}")

    try:
        df = pd.read_csv(output_path)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        raise

    if df.empty:
        logger.error("Baseline CSV is empty.")
        raise ValueError("Baseline CSV is empty.")

    # Check for required columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Check for non-null values in required columns
    total_rows = len(df)
    valid_rows = 0

    for idx, row in df.iterrows():
        is_valid = True
        for col in REQUIRED_COLUMNS:
            val = row[col]
            # Check for NaN, None, or empty string
            if pd.isna(val) or (isinstance(val, str) and val.strip() == ""):
                is_valid = False
                break
        
        if is_valid:
            valid_rows += 1

    completion_rate = valid_rows / total_rows if total_rows > 0 else 0.0

    logger.info(f"Total rows: {total_rows}, Valid rows: {valid_rows}, Completion rate: {completion_rate:.2%}")

    if completion_rate < threshold:
        logger.error(f"Validation FAILED: Completion rate {completion_rate:.2%} is below threshold {threshold:.2%}")
        return False

    logger.info(f"Validation PASSED: Completion rate {completion_rate:.2%} meets threshold {threshold:.2%}")
    return True

def main():
    """Entry point for command-line execution."""
    try:
        success = validate_baseline()
        if success:
            print("Baseline validation successful.")
            sys.exit(0)
        else:
            print("Baseline validation failed.")
            sys.exit(1)
    except Exception as e:
        logger.exception("Validation process failed with exception:")
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()