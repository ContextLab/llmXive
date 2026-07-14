"""
T016: Validate schema of data/processed/features.csv.

Checks:
1. File exists.
2. Required columns are present.
3. No null values in critical columns.
4. Median RT is within valid range (100ms - 2000ms).
5. Power values are non-negative.

Exit Code:
0: Validation passed.
1: Validation failed (logs specific errors).
"""
import os
import sys
import argparse
import pandas as pd
from pathlib import Path

# Import config for paths
from config import get_path

REQUIRED_COLUMNS = [
    'participant_id',
    'median_rt_ms',
    'delta_rel_power',
    'theta_rel_power',
    'alpha_rel_power',
    'beta_low_rel_power',
    'beta_high_rel_power',
    'gamma_rel_power'
]

# RT constraints from spec FR-004
RT_MIN_MS = 100.0
RT_MAX_MS = 2000.0

def validate_schema(input_path: str) -> bool:
    """
    Validates the features CSV against the project schema.
    Returns True if valid, False otherwise.
    """
    errors = []
    path_obj = Path(input_path)

    # 1. Check file existence
    if not path_obj.exists():
        errors.append(f"CRITICAL: File not found: {input_path}")
        print("\n".join(errors))
        return False

    print(f"Loading {input_path}...")
    try:
        df = pd.read_csv(path_obj)
    except Exception as e:
        errors.append(f"CRITICAL: Failed to read CSV: {e}")
        print("\n".join(errors))
        return False

    print(f"Loaded {len(df)} rows, {len(df.columns)} columns.")

    # 2. Check required columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        errors.append(f"Schema Error: Missing required columns: {missing_cols}")
        errors.append(f"Found columns: {list(df.columns)}")

    # 3. Check for nulls in critical columns
    null_checks = {
        'participant_id': 'ID',
        'median_rt_ms': 'RT',
        'delta_rel_power': 'Delta Power',
        'theta_rel_power': 'Theta Power',
        'alpha_rel_power': 'Alpha Power',
        'beta_low_rel_power': 'Low Beta Power',
        'beta_high_rel_power': 'High Beta Power',
        'gamma_rel_power': 'Gamma Power'
    }

    for col, name in null_checks.items():
        if col in df.columns:
            null_count = df[col].isna().sum()
            if null_count > 0:
                errors.append(f"Data Integrity: Column '{name}' ({col}) has {null_count} null values.")

    # 4. Validate RT range
    if 'median_rt_ms' in df.columns:
        rt_series = df['median_rt_ms']
        out_of_range = rt_series[(rt_series < RT_MIN_MS) | (rt_series > RT_MAX_MS)]
        if len(out_of_range) > 0:
            errors.append(f"Data Integrity: Found {len(out_of_range)} participants with RT outside [{RT_MIN_MS}, {RT_MAX_MS}]ms.")
            errors.append(f"Min RT in data: {rt_series.min()}, Max RT in data: {rt_series.max()}")

    # 5. Validate power values (should be >= 0)
    power_cols = [c for c in REQUIRED_COLUMNS if 'power' in c]
    for col in power_cols:
        if col in df.columns:
            neg_count = (df[col] < 0).sum()
            if neg_count > 0:
                errors.append(f"Data Integrity: Column '{col}' has {neg_count} negative values.")

    if errors:
        print("\n--- VALIDATION FAILED ---")
        for err in errors:
            print(f"  [ERROR] {err}")
        return False
    
    print("\n--- VALIDATION PASSED ---")
    print(f"  - File: {input_path}")
    print(f"  - Rows: {len(df)}")
    print(f"  - Columns: {len(df.columns)}")
    print(f"  - No nulls in critical fields")
    print(f"  - RT range valid: [{RT_MIN_MS}, {RT_MAX_MS}]ms")
    print(f"  - Power values non-negative")
    return True

def main():
    parser = argparse.ArgumentParser(description="Validate features.csv schema")
    parser.add_argument(
        "--input", 
        type=str, 
        default=None,
        help="Path to features.csv. Defaults to data/processed/features.csv"
    )
    args = parser.parse_args()

    if args.input:
        input_path = args.input
    else:
        input_path = str(get_path("features"))

    success = validate_schema(input_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()