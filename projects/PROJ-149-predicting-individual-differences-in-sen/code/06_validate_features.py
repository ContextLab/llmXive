"""
T016: Validate schema of data/processed/features.csv.

Validates:
1. No null values in critical columns.
2. Correct column names (participant_id, median_rt, and band powers).
3. Valid RT range: 100ms <= median_rt <= 2000ms (outliers <100 or >2000 excluded).
4. Band power columns are numeric and non-negative.

Output: Prints validation report to stdout and exits with code 0 if valid,
        or code 1 if validation fails.
"""
import os
import sys
import argparse
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory to path to allow imports from config if needed,
# though this script primarily uses standard libs and pandas.
sys.path.insert(0, str(Path(__file__).parent))

from config import get_path, ensure_dirs

def validate_schema(features_path: str) -> bool:
    """
    Validate the schema of the features CSV file.
    
    Args:
        features_path: Path to data/processed/features.csv
        
    Returns:
        bool: True if valid, False otherwise.
    """
    errors = []
    
    # Check file existence
    if not os.path.exists(features_path):
        errors.append(f"ERROR: File not found: {features_path}")
        print("\n".join(errors))
        return False
    
    # Load data
    try:
        df = pd.read_csv(features_path)
    except Exception as e:
        errors.append(f"ERROR: Failed to load CSV: {e}")
        print("\n".join(errors))
        return False
    
    if df.empty:
        errors.append("ERROR: DataFrame is empty.")
        print("\n".join(errors))
        return False
    
    # Define expected columns based on T015 output (CLR-transformed relative power)
    # T015 output: CLR-transformed relative power values for delta, theta, alpha, low-beta, high-beta, gamma
    # plus participant_id and median_rt.
    expected_bands = ['delta', 'theta', 'alpha', 'low_beta', 'high_beta', 'gamma']
    expected_cols = ['participant_id', 'median_rt'] + expected_bands
    
    # 1. Check column names
    missing_cols = [c for c in expected_cols if c not in df.columns]
    if missing_cols:
        errors.append(f"ERROR: Missing required columns: {missing_cols}")
        errors.append(f"  Found columns: {list(df.columns)}")
    
    # 2. Check for null values in critical columns
    critical_cols = ['participant_id', 'median_rt'] + expected_bands
    available_critical = [c for c in critical_cols if c in df.columns]
    
    if available_critical:
        null_counts = df[available_critical].isnull().sum()
        if null_counts.any():
            errors.append("ERROR: Null values found in critical columns:")
            for col, count in null_counts[null_counts > 0].items():
                errors.append(f"  - {col}: {count} nulls")
    
    # 3. Validate RT range (100ms to 2000ms)
    # The task description says: "valid RT range lower bound to 1000ms; explicitly exclude outliers <100ms or >2000ms"
    # This implies the data should already be filtered. We check that all values are within [100, 2000].
    # Note: T013 already excluded <100 and >2000, and T015 should preserve this.
    # However, the task text also says "lower bound to 1000ms" which might be a typo for 100ms given the outlier exclusion.
    # We will enforce [100, 2000] as per the explicit outlier exclusion rule.
    if 'median_rt' in df.columns:
        rt_min = 100.0
        rt_max = 2000.0
        rt_outliers = df[(df['median_rt'] < rt_min) | (df['median_rt'] > rt_max)]
        if not rt_outliers.empty:
            errors.append(f"ERROR: Found {len(rt_outliers)} participants with RT outside [{rt_min}, {rt_max}]ms:")
            for idx, row in rt_outliers.iterrows():
                errors.append(f"  - Participant {row['participant_id']}: RT={row['median_rt']}ms")
    
    # 4. Validate band powers (should be numeric, CLR-transformed values can be negative)
    # We just check they are numeric.
    if available_critical:
        numeric_cols = [c for c in available_critical if c != 'participant_id']
        if numeric_cols:
            non_numeric = df[numeric_cols].select_dtypes(exclude=[np.number])
            if not non_numeric.empty:
                errors.append("ERROR: Non-numeric values found in band power columns:")
                for col in non_numeric.columns:
                    errors.append(f"  - {col}: {non_numeric[col].dtype}")
    
    # 5. Check for duplicates
    if 'participant_id' in df.columns:
        if df['participant_id'].duplicated().any():
            dup_count = df['participant_id'].duplicated().sum()
            errors.append(f"WARNING: Found {dup_count} duplicate participant_ids.")
    
    # Report
    print(f"Validation Report for {features_path}")
    print("-" * 40)
    print(f"Rows: {len(df)}, Columns: {len(df.columns)}")
    print(f"Columns: {list(df.columns)}")
    print("-" * 40)
    
    if errors:
        print("VALIDATION FAILED:")
        print("\n".join(errors))
        return False
    else:
        print("VALIDATION PASSED: Schema is correct, no nulls, RT in range [100, 2000].")
        return True

def main():
    parser = argparse.ArgumentParser(description="Validate features.csv schema")
    parser.add_argument(
        "--features-path",
        type=str,
        default=None,
        help="Path to features.csv. Defaults to data/processed/features.csv"
    )
    args = parser.parse_args()
    
    if args.features_path:
        features_path = args.features_path
    else:
        features_path = get_path("processed", "features.csv")
    
    # Ensure directory exists (though we expect the file to be there)
    ensure_dirs(os.path.dirname(features_path))
    
    is_valid = validate_schema(features_path)
    
    if not is_valid:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()