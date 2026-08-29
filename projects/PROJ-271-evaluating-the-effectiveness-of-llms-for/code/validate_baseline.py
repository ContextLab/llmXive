import os
import sys
import logging
import pandas as pd
from pathlib import Path
from code.config import get_data_path, setup_logging

# Ensure the parent directory is in the path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    "code",
    "loc",
    "cyclomatic_complexity",
    "static_smell_labels"
]

def validate_baseline(filepath: str = None, min_coverage: float = 0.95) -> bool:
    """
    Validates that the static baseline CSV contains at least `min_coverage` (default 95%)
    of the sampled functions with all required columns populated.

    Args:
        filepath: Path to the static_baseline.csv. Defaults to data/static_baseline.csv.
        min_coverage: Minimum fraction of rows that must be valid (0.0 to 1.0).

    Returns:
        bool: True if validation passes, False otherwise.

    Raises:
        FileNotFoundError: If the baseline file does not exist.
        ValueError: If the file is empty or has no valid rows.
    """
    if filepath is None:
        data_dir = get_data_path()
        filepath = os.path.join(data_dir, "static_baseline.csv")

    logger.info(f"Validating baseline file: {filepath}")

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Baseline file not found at {filepath}")

    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        raise ValueError(f"Failed to read CSV file: {e}")

    if df.empty:
        raise ValueError("Baseline CSV is empty.")

    # Check for required columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    total_rows = len(df)
    logger.info(f"Total rows in baseline: {total_rows}")

    # Check for non-null values in required columns
    # We consider a row valid if ALL required columns have non-null, non-empty values
    # For 'code', we check if it's not NaN and not empty string
    # For numeric columns, we check if they are not NaN
    # For 'static_smell_labels', we check if it's not NaN and not empty string

    valid_count = 0
    for index, row in df.iterrows():
        is_valid = True
        
        # Check 'code'
        if pd.isna(row['code']) or (isinstance(row['code'], str) and row['code'].strip() == ""):
            is_valid = False
        
        # Check 'loc'
        if pd.isna(row['loc']):
            is_valid = False

        # Check 'cyclomatic_complexity'
        if pd.isna(row['cyclomatic_complexity']):
            is_valid = False

        # Check 'static_smell_labels'
        if pd.isna(row['static_smell_labels']) or (isinstance(row['static_smell_labels'], str) and row['static_smell_labels'].strip() == ""):
            is_valid = False

        if is_valid:
            valid_count += 1

    coverage = valid_count / total_rows
    logger.info(f"Valid rows: {valid_count} / {total_rows} (Coverage: {coverage:.2%})")

    if coverage < min_coverage:
        logger.error(f"Validation FAILED: Coverage {coverage:.2%} is below required {min_coverage:.2%}")
        return False
    
    logger.info(f"Validation PASSED: Coverage {coverage:.2%} meets requirement of {min_coverage:.2%}")
    return True

def main():
    """
    Entry point for running the validation as a script.
    """
    setup_logging()
    try:
        success = validate_baseline()
        if success:
            print("SUCCESS: Baseline validation passed.")
            sys.exit(0)
        else:
            print("FAILURE: Baseline validation failed.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Validation process failed with error: {e}")
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()