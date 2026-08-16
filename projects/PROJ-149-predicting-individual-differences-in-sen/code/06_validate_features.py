"""
T035a: Validate schema of data/processed/features.csv

Validates:
- File exists
- Required columns present
- No null values
- RT range validity (100ms to 2000ms) as per FR-004
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
from pathlib import Path

# Import from config for paths
from config import get_path, ensure_dirs


def validate_schema():
    """
    Validate the schema of data/processed/features.csv.

    Checks:
    1. File exists
    2. Required columns: participant_id, median_rt, delta, theta, alpha, low_beta, high_beta, gamma
       (relative power values as per T015)
    3. No null values in any column
    4. median_rt in valid range [100, 2000] ms (FR-004)
    5. Power values are non-negative

    Returns:
        bool: True if validation passes, False otherwise
    """
    # Get path to features file
    features_path = get_path("processed", "features.csv")
    print(f"Validating schema for: {features_path}")

    # Check file exists
    if not os.path.exists(features_path):
        print(f"ERROR: File not found: {features_path}")
        return False

    # Load data
    try:
        df = pd.read_csv(features_path)
    except Exception as e:
        print(f"ERROR: Failed to load CSV: {e}")
        return False

    print(f"Loaded {len(df)} rows, {len(df.columns)} columns")

    # Define required columns (relative power bands + RT + ID)
    # T015 produces relative power: delta, theta, alpha, low_beta, high_beta, gamma
    required_columns = [
        'participant_id',
        'median_rt',
        'delta', 'theta', 'alpha', 'low_beta', 'high_beta', 'gamma'
    ]

    # Check required columns
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        print(f"ERROR: Missing required columns: {missing_cols}")
        return False

    print("✓ All required columns present")

    # Check for null values
    null_counts = df.isnull().sum()
    null_cols = null_counts[null_counts > 0]
    if len(null_cols) > 0:
        print(f"ERROR: Null values found in columns: {null_cols.to_dict()}")
        return False

    print("✓ No null values found")

    # Validate RT range (FR-004: 100ms to 2000ms)
    rt_col = 'median_rt'
    rt_min = df[rt_col].min()
    rt_max = df[rt_col].max()
    rt_invalid = df[(df[rt_col] < 100) | (df[rt_col] > 2000)]

    if len(rt_invalid) > 0:
        print(f"ERROR: {len(rt_invalid)} rows have invalid RT values (<100ms or >2000ms)")
        print(f"RT range in data: {rt_min}ms to {rt_max}ms")
        return False

    print(f"✓ RT values in valid range: {rt_min}ms to {rt_max}ms")

    # Validate power values are non-negative
    power_cols = ['delta', 'theta', 'alpha', 'low_beta', 'high_beta', 'gamma']
    for col in power_cols:
        if (df[col] < 0).any():
            print(f"ERROR: Negative values found in {col}")
            return False

    print("✓ All power values are non-negative")

    # Validate participant_id is not empty
    if df['participant_id'].astype(str).str.strip().eq('').any():
        print("ERROR: Empty participant_id found")
        return False

    print("✓ All participant_ids are valid")

    # Generate validation report
    report_path = get_path("processed", "validation_report.json")
    ensure_dirs(report_path)

    report = {
        "file": str(features_path),
        "status": "PASS",
        "row_count": len(df),
        "column_count": len(df.columns),
        "rt_range": {"min": float(rt_min), "max": float(rt_max)},
        "columns_validated": required_columns,
        "checks": {
            "file_exists": True,
            "columns_present": True,
            "no_nulls": True,
            "rt_range_valid": True,
            "power_non_negative": True,
            "participant_ids_valid": True
        }
    }

    import json
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"✓ Validation report written to: {report_path}")
    print("✓ SCHEMA VALIDATION PASSED")

    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate features.csv schema")
    parser.add_argument("--path", type=str, default=None, help="Override path to features file")
    args = parser.parse_args()

    success = validate_schema()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
