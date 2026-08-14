"""
T035a: Validate schema of data/processed/features.csv
Checks: no nulls, correct columns, valid RT range (150ms to 1000ms).
Explicitly excludes outliers <100ms or >2000ms (as per task description).
"""
import os
import sys
import argparse
import pandas as pd
import numpy as np
from pathlib import Path

# Import config utilities to handle path resolution robustly
# We import the specific symbols we need from config.py
# Note: config.py defines get_path and ensure_dirs with flexible signatures
try:
    from config import get_path, ensure_dirs
except ImportError:
    # Fallback for direct execution if config is not in path (unlikely in this structure)
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))
    from config import get_path, ensure_dirs

# Define expected columns based on T015 output (CLR-transformed relative power + RT)
# T015 produces: participant_id, median_rt, and relative power bands (delta, theta, alpha, low_beta, high_beta, gamma)
# The task description mentions "valid RT range", implying 'median_rt' or similar column exists.
EXPECTED_COLUMNS = {
    'participant_id',
    'median_rt',
    'delta',
    'theta',
    'alpha',
    'low_beta',
    'high_beta',
    'gamma'
}

# RT Validation thresholds
# Task T035a says: "valid RT range 150ms to 1000ms"
# AND "explicitly exclude outliers <100ms or >2000ms"
# This implies the validation should check if values fall within the "valid" range (150-1000)
# and report any that are outside, or specifically check that the data *used* was filtered correctly.
# Given the instruction "Validate schema... (no nulls, correct columns, valid RT range...)",
# we will check that all RT values are within [150, 1000].
# If any are <100 or >2000, that is a critical failure of upstream filtering (T013).
RT_MIN_VALID = 150.0
RT_MAX_VALID = 1000.0
RT_CRITICAL_LOW = 100.0
RT_CRITICAL_HIGH = 2000.0

def validate_schema(input_path: str) -> bool:
    """
    Validates the schema and content of the features CSV.
    Returns True if valid, False otherwise.
    Raises RuntimeError with details if validation fails.
    """
    path_obj = Path(input_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        raise RuntimeError(f"Failed to read CSV: {e}")

    if df.empty:
        raise RuntimeError("Input file is empty.")

    # 1. Check Columns
    existing_cols = set(df.columns)
    missing_cols = EXPECTED_COLUMNS - existing_cols
    if missing_cols:
        raise RuntimeError(f"Missing required columns: {missing_cols}. Found: {list(df.columns)}")

    # 2. Check for Nulls
    null_counts = df.isnull().sum()
    if null_counts.any():
        null_cols = null_counts[null_counts > 0].index.tolist()
        raise RuntimeError(f"Null values found in columns: {null_cols}")

    # 3. Validate RT Range
    rt_col = 'median_rt'
    if rt_col not in df.columns:
        raise RuntimeError(f"RT column '{rt_col}' not found.")

    rt_series = df[rt_col]

    # Check for critical outliers (<100 or >2000) - this indicates a failure in T013
    critical_outliers = df[(rt_series < RT_CRITICAL_LOW) | (rt_series > RT_CRITICAL_HIGH)]
    if not critical_outliers.empty:
        count = len(critical_outliers)
        raise RuntimeError(
            f"CRITICAL: Found {count} participants with RTs outside the allowed range (<{RT_CRITICAL_LOW}ms or >{RT_CRITICAL_HIGH}ms). "
            f"This indicates T013 (behavioral parsing) failed to filter outliers correctly."
        )

    # Check for "valid" range (150 to 1000) as per T035a description
    invalid_range = df[(rt_series < RT_MIN_VALID) | (rt_series > RT_MAX_VALID)]
    if not invalid_range.empty:
        count = len(invalid_range)
        # These are outside the "valid" range for analysis, but not necessarily "critical" errors if T013 allowed them
        # However, T035a says "valid RT range 150ms to 1000ms", implying we should enforce this.
        # If the task is to validate that the data *meets* this criteria, we fail if they don't.
        raise RuntimeError(
            f"Validation Failed: Found {count} participants with RTs outside the valid analysis range (150ms - 1000ms). "
            f"Range: [{rt_series.min()}, {rt_series.max()}]. "
            f"All values must be between {RT_MIN_VALID} and {RT_MAX_VALID}."
        )

    # 4. Validate Power Values (Sanity Check)
    # Power values (even CLR transformed) should be numeric and finite
    power_cols = ['delta', 'theta', 'alpha', 'low_beta', 'high_beta', 'gamma']
    for col in power_cols:
        if not np.isfinite(df[col]).all():
            raise RuntimeError(f"Non-finite values (inf/nan) found in power column: {col}")

    print(f"Schema validation PASSED for {input_path}")
    print(f"  - Rows: {len(df)}")
    print(f"  - Columns: {list(df.columns)}")
    print(f"  - RT Range: [{rt_series.min():.2f}, {rt_series.max():.2f}]")
    return True

def main():
    parser = argparse.ArgumentParser(description="Validate features.csv schema and content.")
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to features.csv. If not provided, uses config path."
    )
    parser.add_argument(
        "--output-log",
        type=str,
        default=None,
        help="Path to write validation log (optional)."
    )

    args = parser.parse_args()

    # Resolve input path
    if args.input:
        input_path = args.input
    else:
        # Try to get path from config. T015 outputs to data/processed/features.csv
        # Config might have a key for 'features' or we construct it.
        # Based on T035a description: "data/processed/features.csv"
        try:
            # Attempt to use config's get_path if it supports string keys
            # The config.py signature is flexible, but we try a standard key first
            input_path = get_path("data/processed/features.csv")
        except (ValueError, TypeError):
            # Fallback to hardcoded relative path if config key fails
            input_path = os.path.join("data", "processed", "features.csv")

    # Ensure output directory exists if logging
    if args.output_log:
        ensure_dirs(args.output_log)

    try:
        is_valid = validate_schema(input_path)
        if is_valid:
            print("Validation successful.")
            sys.exit(0)
        else:
            # Should have raised an error if invalid, but just in case
            print("Validation failed.")
            sys.exit(1)
    except Exception as e:
        print(f"Validation FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()