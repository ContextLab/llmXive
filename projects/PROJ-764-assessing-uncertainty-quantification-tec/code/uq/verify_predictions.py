"""
Task T018: Verify results/uq_predictions.csv generation and schema compliance.

This script validates that the UQ predictions file exists, has the correct columns,
and contains non-empty, valid data.
"""
import os
import sys
import json
import pandas as pd
import numpy as np

# Define the expected file path and schema
OUTPUT_PATH = "results/uq_predictions.csv"
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

def verify_schema(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """Check if the DataFrame has the required columns."""
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    extra = [col for col in df.columns if col not in REQUIRED_COLUMNS]
    
    if missing:
        return False, [f"Missing columns: {missing}"]
    
    issues = []
    if extra:
        issues.append(f"Extra columns found (allowed but noted): {extra}")
    
    # Check for data types
    numeric_cols = ["prediction", "variance", "lower_50", "upper_50", "lower_90", "upper_90"]
    for col in numeric_cols:
        if not pd.api.types.is_numeric_dtype(df[col]):
            issues.append(f"Column '{col}' is not numeric.")
    
    return len(issues) == 0, issues

def verify_data_integrity(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """Check for NaNs, infinite values, and logical consistency."""
    issues = []
    
    # Check for empty dataframe
    if df.empty:
        return False, ["DataFrame is empty."]
    
    # Check for NaNs
    null_counts = df.isnull().sum()
    if null_counts.any():
        cols_with_nulls = null_counts[null_counts > 0].index.tolist()
        issues.append(f"Columns with null values: {cols_with_nulls}")
    
    # Check for infinite values
    numeric_cols = ["prediction", "variance", "lower_50", "upper_50", "lower_90", "upper_90"]
    for col in numeric_cols:
        if np.isinf(df[col]).any():
            issues.append(f"Column '{col}' contains infinite values.")
    
    # Logical consistency: lower <= prediction <= upper
    # 50% bounds
    if not (df["lower_50"] <= df["prediction"]).all():
        issues.append("lower_50 > prediction for some rows.")
    if not (df["prediction"] <= df["upper_50"]).all():
        issues.append("prediction > upper_50 for some rows.")
    
    # 90% bounds
    if not (df["lower_90"] <= df["prediction"]).all():
        issues.append("lower_90 > prediction for some rows.")
    if not (df["prediction"] <= df["upper_90"]).all():
        issues.append("prediction > upper_90 for some rows.")
    
    # 90% bounds should be wider than 50% bounds
    if not (df["lower_90"] <= df["lower_50"]).all():
        issues.append("lower_90 > lower_50 for some rows (invalid interval hierarchy).")
    if not (df["upper_50"] <= df["upper_90"]).all():
        issues.append("upper_50 > upper_90 for some rows (invalid interval hierarchy).")
    
    # Variance should be non-negative
    if (df["variance"] < 0).any():
        issues.append("Negative variance values found.")
    
    return len(issues) == 0, issues

def main():
    print(f"Verifying {OUTPUT_PATH}...")
    
    # 1. Check file existence
    if not os.path.exists(OUTPUT_PATH):
        print(f"ERROR: File not found: {OUTPUT_PATH}")
        sys.exit(1)
    
    # 2. Load data
    try:
        df = pd.read_csv(OUTPUT_PATH)
        print(f"Loaded {len(df)} rows.")
    except Exception as e:
        print(f"ERROR: Failed to load CSV: {e}")
        sys.exit(1)
    
    # 3. Verify Schema
    schema_ok, schema_issues = verify_schema(df)
    if not schema_ok:
        print("Schema Verification FAILED:")
        for issue in schema_issues:
            print(f"  - {issue}")
        sys.exit(1)
    print("Schema Verification PASSED.")
    
    # 4. Verify Data Integrity
    integrity_ok, integrity_issues = verify_data_integrity(df)
    if not integrity_ok:
        print("Data Integrity Verification FAILED:")
        for issue in integrity_issues:
            print(f"  - {issue}")
        sys.exit(1)
    print("Data Integrity Verification PASSED.")
    
    # 5. Summary
    methods = df["method"].unique().tolist()
    print(f"Verification Complete. Methods present: {methods}")
    print("All checks passed.")
    sys.exit(0)

if __name__ == "__main__":
    main()