"""
Verification script for T018: Verify uq_predictions_base.csv generation and schema compliance.

This script validates that the main pipeline output (results/uq_predictions_base.csv)
exists, is non-empty, and strictly adheres to the required schema defined in T016a.

Schema Requirements:
- Columns: sample_id, method, prediction, variance, lower_50, upper_50, lower_90, upper_90
- sample_id: int
- method: str
- prediction, variance, lower_50, upper_50, lower_90, upper_90: float64
"""
import os
import sys
import json
import pandas as pd
import numpy as np
from typing import Dict, Any, List

# Constants
OUTPUT_PATH = "results/uq_predictions_base.csv"
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
REQUIRED_DTYPES = {
    "sample_id": "int64",
    "method": "object",
    "prediction": "float64",
    "variance": "float64",
    "lower_50": "float64",
    "upper_50": "float64",
    "lower_90": "float64",
    "upper_90": "float64"
}

def verify_schema(df: pd.DataFrame) -> List[str]:
    """
    Verify the DataFrame schema matches requirements.
    
    Args:
        df: The loaded DataFrame.
        
    Returns:
        A list of error messages. Empty if valid.
    """
    errors = []
    
    # Check columns
    if list(df.columns) != REQUIRED_COLUMNS:
        missing = set(REQUIRED_COLUMNS) - set(df.columns)
        extra = set(df.columns) - set(REQUIRED_COLUMNS)
        errors.append(f"Column mismatch. Missing: {missing}, Extra: {extra}")
    
    # Check dtypes
    for col, expected_dtype in REQUIRED_DTYPES.items():
        if col in df.columns:
            actual_dtype = str(df[col].dtype)
            # Allow some flexibility for object vs string, but strict on floats/ints
            if expected_dtype == "object" and actual_dtype not in ["object", "string"]:
                errors.append(f"Column '{col}': expected object, got {actual_dtype}")
            elif expected_dtype == "int64" and not np.issubdtype(df[col].dtype, np.integer):
                errors.append(f"Column '{col}': expected int64, got {actual_dtype}")
            elif expected_dtype == "float64" and not np.issubdtype(df[col].dtype, np.floating):
                errors.append(f"Column '{col}': expected float64, got {actual_dtype}")
    
    return errors

def verify_data_integrity(df: pd.DataFrame) -> List[str]:
    """
    Verify data integrity (no nulls where required, valid ranges).
    
    Args:
        df: The loaded DataFrame.
        
    Returns:
        A list of error messages. Empty if valid.
    """
    errors = []
    
    # Check for nulls
    for col in REQUIRED_COLUMNS:
        if col in df.columns:
            if df[col].isnull().any():
                errors.append(f"Column '{col}' contains null values.")
    
    # Check variance is non-negative
    if "variance" in df.columns and (df["variance"] < 0).any():
        errors.append("Column 'variance' contains negative values.")
    
    # Check bounds consistency (lower < pred < upper)
    # Allow small floating point tolerance
    tol = 1e-9
    if "lower_50" in df.columns and "upper_50" in df.columns:
        if ((df["lower_50"] - df["upper_50"]) > tol).any():
            errors.append("Column 'lower_50' is greater than 'upper_50' in some rows.")
    
    if "lower_90" in df.columns and "upper_90" in df.columns:
        if ((df["lower_90"] - df["upper_90"]) > tol).any():
            errors.append("Column 'lower_90' is greater than 'upper_90' in some rows.")
    
    # Check interval nesting (90% should be wider than 50%)
    if all(c in df.columns for c in ["lower_50", "upper_50", "lower_90", "upper_90"]):
        width_50 = df["upper_50"] - df["lower_50"]
        width_90 = df["upper_90"] - df["lower_90"]
        if (width_50 > width_90 + tol).any():
            errors.append("50% confidence interval is wider than 90% interval in some rows.")
    
    return errors

def main():
    """Main entry point for verification."""
    print(f"Verifying {OUTPUT_PATH}...")
    
    # 1. Check file existence
    if not os.path.exists(OUTPUT_PATH):
        print(f"ERROR: File not found: {OUTPUT_PATH}")
        sys.exit(1)
    
    # 2. Load data
    try:
        df = pd.read_csv(OUTPUT_PATH)
    except Exception as e:
        print(f"ERROR: Failed to load CSV: {e}")
        sys.exit(1)
    
    # 3. Check non-empty
    if df.empty:
        print("ERROR: CSV file is empty.")
        sys.exit(1)
    
    print(f"Loaded {len(df)} rows.")
    
    # 4. Verify Schema
    schema_errors = verify_schema(df)
    if schema_errors:
        print("Schema Verification FAILED:")
        for err in schema_errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("Schema Verification PASSED.")
    
    # 5. Verify Data Integrity
    integrity_errors = verify_data_integrity(df)
    if integrity_errors:
        print("Data Integrity Verification FAILED:")
        for err in integrity_errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("Data Integrity Verification PASSED.")
    
    # 6. Summary
    print(f"\n✅ SUCCESS: {OUTPUT_PATH} is valid.")
    print(f"   - Rows: {len(df)}")
    print(f"   - Columns: {list(df.columns)}")
    print(f"   - Methods present: {df['method'].unique().tolist()}")
    sys.exit(0)

if __name__ == "__main__":
    main()