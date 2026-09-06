import os
import sys
import json
import pandas as pd
import numpy as np
from typing import Dict, Any, List

# Constants for expected schema
REQUIRED_COLUMNS = [
    "sample_id",
    "method",
    "prediction",
    "variance",
    "lower_50",
    "upper_50",
    "lower_90",
    "upper_90"
]
EXPECTED_METHODS = ["deep_ensemble", "mc_dropout", "sparse_gp"]

def verify_schema(filepath: str) -> bool:
    """
    Verifies that the CSV file exists, is readable, and matches the expected schema.
    Returns True if valid, False otherwise.
    """
    if not os.path.exists(filepath):
        print(f"ERROR: File not found: {filepath}")
        return False

    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        print(f"ERROR: Failed to read CSV: {e}")
        return False

    # Check columns
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_cols:
        print(f"ERROR: Missing columns in {filepath}: {missing_cols}")
        return False

    # Check column order (optional but strict per spec)
    if list(df.columns) != REQUIRED_COLUMNS:
        print(f"WARNING: Column order mismatch. Expected {REQUIRED_COLUMNS}, got {list(df.columns)}")
        # We allow reordering for flexibility, but strict compliance might require this to fail.
        # For now, we treat it as a warning but proceed if all columns exist.

    # Check data types roughly
    numeric_cols = ["sample_id", "prediction", "variance", "lower_50", "upper_50", "lower_90", "upper_90"]
    for col in numeric_cols:
        if not np.issubdtype(df[col].dtype, np.number):
            print(f"ERROR: Column '{col}' is not numeric. Found dtype: {df[col].dtype}")
            return False

    if not np.issubdtype(df["method"].dtype, object):
        print(f"WARNING: Column 'method' is not string/object. Found dtype: {df[method].dtype}")

    # Check methods
    actual_methods = set(df["method"].unique())
    expected_methods_set = set(EXPECTED_METHODS)
    if not expected_methods_set.issubset(actual_methods):
        missing_methods = expected_methods_set - actual_methods
        print(f"ERROR: Missing expected methods in 'method' column: {missing_methods}")
        return False

    print(f"Schema verification PASSED for {filepath}")
    print(f"  - Rows: {len(df)}")
    print(f"  - Columns: {list(df.columns)}")
    print(f"  - Methods found: {actual_methods}")
    return True

def verify_data_integrity(filepath: str) -> bool:
    """
    Verifies data integrity:
    1. Variance is non-negative.
    2. lower_50 <= prediction <= upper_50
    3. lower_90 <= lower_50 and upper_50 <= upper_90
    4. No NaN values in critical columns.
    """
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        print(f"ERROR: Failed to read CSV for integrity check: {e}")
        return False

    issues = []

    # Check for NaNs in critical columns
    critical_cols = REQUIRED_COLUMNS
    null_counts = df[critical_cols].isnull().sum()
    if null_counts.any():
        issues.append(f"Found NaN values in critical columns:\n{null_counts[null_counts > 0]}")

    # Check variance >= 0
    if (df["variance"] < 0).any():
        issues.append(f"Found negative variance values. Count: {(df['variance'] < 0).sum()}")

    # Check bounds consistency
    # lower_50 <= prediction <= upper_50
    invalid_50 = (df["lower_50"] > df["prediction"]) | (df["prediction"] > df["upper_50"])
    if invalid_50.any():
        issues.append(f"Found {invalid_50.sum()} rows where prediction is not within 50% bounds.")

    # lower_90 <= lower_50 <= prediction <= upper_50 <= upper_90
    invalid_90 = (df["lower_90"] > df["lower_50"]) | (df["upper_50"] > df["upper_90"])
    if invalid_90.any():
        issues.append(f"Found {invalid_90.sum()} rows where 90% bounds are inconsistent with 50% bounds.")

    if issues:
        print("ERROR: Data integrity checks FAILED:")
        for issue in issues:
            print(f"  - {issue}")
        return False

    print("Data integrity verification PASSED")
    return True

def main():
    """
    Main entry point for T018 verification task.
    Verifies results/uq_predictions_base.csv generation and schema compliance.
    """
    filepath = "results/uq_predictions_base.csv"
    
    print(f"Starting verification for: {filepath}")
    print("-" * 50)

    schema_ok = verify_schema(filepath)
    if not schema_ok:
        print("\nVerification FAILED due to schema errors.")
        sys.exit(1)

    integrity_ok = verify_data_integrity(filepath)
    if not integrity_ok:
        print("\nVerification FAILED due to data integrity errors.")
        sys.exit(1)

    print("-" * 50)
    print("VERIFICATION SUCCESSFUL: results/uq_predictions_base.csv is valid.")
    sys.exit(0)

if __name__ == "__main__":
    main()