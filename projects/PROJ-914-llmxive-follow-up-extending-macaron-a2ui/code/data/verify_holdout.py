"""
Verification script for the N=50 human-annotated hold-out set.

This script validates the existence and correctness of the hold-out dataset
required as a blocking prerequisite for User Story 2 (Simulation).

It checks:
1. File existence at the expected path.
2. Exact row count (N=50).
3. Presence of required columns: query, ground_truth_intent, complexity_score.
4. Absence of missing values in critical columns.
5. Validity of label values (High-Confidence, Ambiguous).
6. Validity of complexity_score (numeric, within range).

If any check fails, the script exits with a non-zero status and a clear error.
"""
import os
import sys
import argparse
import logging
from pathlib import Path
import pandas as pd

from config import get_holdout_data_path, ensure_dirs
from utils.logging import get_experiment_logger, log_error, log_info

# Configure logging
logger = get_experiment_logger("verify_holdout")

REQUIRED_COLUMNS = ["query", "ground_truth_intent", "complexity_score"]
VALID_LABELS = {"High-Confidence", "Ambiguous"}
EXPECTED_ROW_COUNT = 50
MIN_COMPLEXITY = 0.0
MAX_COMPLEXITY = 5.0  # Assuming a 0-5 scale based on typical complexity metrics

def verify_file_exists(file_path: Path) -> bool:
    """Check if the hold-out file exists."""
    exists = file_path.exists()
    if exists:
        log_info(logger, f"Hold-out file found: {file_path}")
    else:
        log_error(logger, f"Hold-out file NOT found: {file_path}")
    return exists

def verify_row_count(df: pd.DataFrame, expected: int) -> bool:
    """Check if the dataframe has the expected number of rows."""
    actual = len(df)
    if actual == expected:
        log_info(logger, f"Row count verified: {actual} == {expected}")
        return True
    else:
        log_error(logger, f"Row count mismatch: {actual} != {expected}")
        return False

def verify_columns(df: pd.DataFrame, required: list) -> bool:
    """Check if all required columns are present."""
    missing = [col for col in required if col not in df.columns]
    if not missing:
        log_info(logger, f"All required columns present: {required}")
        return True
    else:
        log_error(logger, f"Missing required columns: {missing}")
        return False

def verify_no_missing_values(df: pd.DataFrame, columns: list) -> bool:
    """Check for missing values in critical columns."""
    has_missing = False
    for col in columns:
        null_count = df[col].isnull().sum()
        if null_count > 0:
            log_error(logger, f"Column '{col}' has {null_count} missing values.")
            has_missing = True
        else:
            log_info(logger, f"Column '{col}' has no missing values.")
    
    if not has_missing:
        log_info(logger, "No missing values in critical columns.")
    return not has_missing

def verify_labels(df: pd.DataFrame, column: str, valid_values: set) -> bool:
    """Check if label values are within the valid set."""
    if column not in df.columns:
        log_error(logger, f"Label column '{column}' not found.")
        return False

    unique_values = set(df[column].unique())
    invalid = unique_values - valid_values
    
    if not invalid:
        log_info(logger, f"Labels verified: all values in {valid_values}")
        return True
    else:
        log_error(logger, f"Invalid labels found: {invalid}")
        return False

def verify_complexity_score(df: pd.DataFrame, column: str, min_val: float, max_val: float) -> bool:
    """Check if complexity scores are within the expected numeric range."""
    if column not in df.columns:
        log_error(logger, f"Complexity column '{column}' not found.")
        return False

    try:
        # Ensure it's numeric
        numeric_col = pd.to_numeric(df[column], errors='coerce')
        invalid_mask = numeric_col.isnull() | (numeric_col < min_val) | (numeric_col > max_val)
        invalid_count = invalid_mask.sum()

        if invalid_count == 0:
            log_info(logger, f"Complexity scores verified: all in [{min_val}, {max_val}]")
            return True
        else:
            log_error(logger, f"Found {invalid_count} complexity scores outside [{min_val}, {max_val}].")
            return False
    except Exception as e:
        log_error(logger, f"Error verifying complexity scores: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Verify N=50 hold-out set validity.")
    parser.add_argument("--path", type=str, default=None, help="Path to hold-out CSV. Defaults to config.")
    args = parser.parse_args()

    # Determine path
    if args.path:
        file_path = Path(args.path)
    else:
        file_path = get_holdout_data_path()

    log_info(logger, f"Starting verification for: {file_path}")

    all_passed = True

    # 1. File Existence
    if not verify_file_exists(file_path):
        all_passed = False
        log_error(logger, "Verification FAILED: File not found.")
        sys.exit(1)

    # Load data
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        log_error(logger, f"Failed to load CSV: {e}")
        sys.exit(1)

    # 2. Row Count
    if not verify_row_count(df, EXPECTED_ROW_COUNT):
        all_passed = False

    # 3. Columns
    if not verify_columns(df, REQUIRED_COLUMNS):
        all_passed = False

    # 4. Missing Values
    if not verify_no_missing_values(df, REQUIRED_COLUMNS):
        all_passed = False

    # 5. Labels
    if not verify_labels(df, "ground_truth_intent", VALID_LABELS):
        all_passed = False

    # 6. Complexity Score
    if not verify_complexity_score(df, "complexity_score", MIN_COMPLEXITY, MAX_COMPLEXITY):
        all_passed = False

    if all_passed:
        log_info(logger, "=== VERIFICATION PASSED ===")
        log_info(logger, "N=50 hold-out set is valid and ready for US2.")
        sys.exit(0)
    else:
        log_error(logger, "=== VERIFICATION FAILED ===")
        log_error(logger, "Hold-out set is invalid. US2 cannot proceed.")
        sys.exit(1)

if __name__ == "__main__":
    main()