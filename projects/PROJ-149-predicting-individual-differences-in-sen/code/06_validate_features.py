"""
T035a: Validate schema of data/processed/features.csv.

Validates:
1. No nulls in any column.
2. Correct columns (participant_id, median_rt, delta, theta, alpha, low_beta, high_beta, gamma, relative_delta, relative_theta, relative_alpha, relative_low_beta, relative_high_beta, relative_gamma).
3. Valid RT range: 150ms to 1000ms (explicitly excludes outliers <100ms or >2000ms).
4. Positive power values.
"""
import os
import sys
import argparse
import pandas as pd
import numpy as np
from pathlib import Path

# Import config utilities
from config import get_path, ensure_dirs

def validate_schema(features_path: str) -> bool:
    """
    Validates the schema and content of the features CSV file.
    
    Args:
        features_path: Path to the features CSV file.
        
    Returns:
        bool: True if validation passes, False otherwise.
    """
    print(f"Validating schema for: {features_path}")
    
    if not os.path.exists(features_path):
        print(f"ERROR: File not found: {features_path}")
        return False
    
    try:
        df = pd.read_csv(features_path)
    except Exception as e:
        print(f"ERROR: Failed to load CSV: {e}")
        return False
    
    print(f"Loaded {len(df)} rows and {len(df.columns)} columns.")
    
    # Define expected columns
    expected_cols = [
        'participant_id', 'median_rt',
        'delta', 'theta', 'alpha', 'low_beta', 'high_beta', 'gamma',
        'relative_delta', 'relative_theta', 'relative_alpha',
        'relative_low_beta', 'relative_high_beta', 'relative_gamma'
    ]
    
    # Check 1: Correct columns
    missing_cols = set(expected_cols) - set(df.columns)
    extra_cols = set(df.columns) - set(expected_cols)
    
    if missing_cols:
        print(f"ERROR: Missing expected columns: {missing_cols}")
        return False
    if extra_cols:
        print(f"WARNING: Extra columns found (not strictly an error, but unexpected): {extra_cols}")
    
    # Check 2: No nulls
    null_counts = df.isnull().sum()
    if null_counts.any():
        print(f"ERROR: Found null values in the following columns:")
        print(null_counts[null_counts > 0])
        return False
    
    # Check 3: Valid RT range (150ms to 1000ms)
    # The task explicitly mentions excluding outliers <100ms or >2000ms in previous steps,
    # but the validation constraint is 150ms to 1000ms.
    rt_col = 'median_rt'
    if rt_col not in df.columns:
        print(f"ERROR: Column '{rt_col}' not found.")
        return False
        
    rt_min = df[rt_col].min()
    rt_max = df[rt_col].max()
    
    if rt_min < 150:
        outliers_low = df[df[rt_col] < 150]
        print(f"ERROR: Found {len(outliers_low)} rows with RT < 150ms (min: {rt_min}).")
        print("Outliers (first 5):")
        print(outliers_low.head())
        return False
        
    if rt_max > 1000:
        outliers_high = df[df[rt_col] > 1000]
        print(f"ERROR: Found {len(outliers_high)} rows with RT > 1000ms (max: {rt_max}).")
        print("Outliers (first 5):")
        print(outliers_high.head())
        return False
        
    print(f"RT range valid: [{rt_min}, {rt_max}]")
    
    # Check 4: Power values should be positive (relative power 0-1, absolute power > 0)
    power_cols = [c for c in df.columns if c in expected_cols and c != 'participant_id' and c != 'median_rt']
    for col in power_cols:
        if (df[col] <= 0).any():
            # Relative power can be 0, but absolute power should be > 0.
            # Let's be strict: all power values must be > 0.
            if col.startswith('relative_'):
                if (df[col] < 0).any():
                     print(f"ERROR: Negative relative power found in {col}.")
                     return False
            else:
                if (df[col] <= 0).any():
                    print(f"ERROR: Non-positive power found in {col}.")
                    return False
    
    print("Schema validation PASSED.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Validate features.csv schema")
    parser.add_argument("--input", type=str, default=None, help="Path to features.csv. Defaults to config path.")
    args = parser.parse_args()
    
    if args.input:
        features_path = args.input
    else:
        # Use config path for processed features
        features_path = get_path("processed", "features.csv")
    
    # Ensure directory exists (though we are reading, not writing, good practice)
    # ensure_dirs(os.path.dirname(features_path)) 
    
    success = validate_schema(features_path)
    
    if not success:
        print("Validation FAILED.")
        sys.exit(1)
    else:
        print("Validation SUCCESS.")
        sys.exit(0)

if __name__ == "__main__":
    main()
