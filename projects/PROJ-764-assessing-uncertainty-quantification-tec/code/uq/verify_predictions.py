import os
import sys
import json
import pandas as pd
import numpy as np
from typing import Dict, Any, List

# Constants for schema validation
REQUIRED_COLUMNS = [
    "sample_id", "method", "prediction", "variance",
    "lower_50", "upper_50", "lower_90", "upper_90",
    "aleatoric", "epistemic", "total", "uncertainty_type"
]

# Expected types for validation
COLUMN_TYPES = {
    "sample_id": "int64",
    "method": "object",
    "prediction": "float64",
    "variance": "float64",
    "lower_50": "float64",
    "upper_50": "float64",
    "lower_90": "float64",
    "upper_90": "float64",
    "aleatoric": "float64",
    "epistemic": "float64",
    "total": "float64",
    "uncertainty_type": "object"
}

def verify_schema(df: pd.DataFrame, filepath: str) -> bool:
    """
    Verify that the DataFrame matches the required schema for uq_predictions.csv.
    
    Checks:
    1. All required columns are present in the exact order.
    2. Column data types match expectations (allowing for nullable floats).
    3. No NaN values in critical columns (sample_id, method, prediction).
    
    Returns:
        bool: True if schema is valid, False otherwise.
    """
    errors = []
    
    # Check column presence
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_cols:
        errors.append(f"Missing columns: {missing_cols}")
    
    # Check column order
    if list(df.columns) != REQUIRED_COLUMNS:
        errors.append(f"Column order mismatch. Expected: {REQUIRED_COLUMNS}, Got: {list(df.columns)}")
    
    # Check data types (allowing for nullable float64)
    for col in REQUIRED_COLUMNS:
        if col in df.columns:
            dtype = df[col].dtype
            expected = COLUMN_TYPES[col]
            # Allow float64 for numeric columns even if they contain NaN (which makes them float64 in pandas)
            if expected == "float64" and str(dtype) not in ["float64", "Float64"]:
                errors.append(f"Column '{col}' has type {dtype}, expected {expected}")
            elif expected == "int64" and str(dtype) not in ["int64", "Int64"]:
                errors.append(f"Column '{col}' has type {dtype}, expected {expected}")
            elif expected == "object" and str(dtype) != "object":
                errors.append(f"Column '{col}' has type {dtype}, expected object")
    
    # Check for critical NaN values
    critical_cols = ["sample_id", "method", "prediction"]
    for col in critical_cols:
        if col in df.columns and df[col].isna().any():
            errors.append(f"Critical column '{col}' contains NaN values")
    
    if errors:
        print(f"Schema validation FAILED for {filepath}:")
        for err in errors:
            print(f"  - {err}")
        return False
    
    print(f"Schema validation PASSED for {filepath}")
    return True

def verify_data_integrity(df: pd.DataFrame, filepath: str) -> bool:
    """
    Verify data integrity constraints for uq_predictions.csv.
    
    Checks:
    1. prediction, variance, bounds are finite (no inf/nan in numeric cols).
    2. lower_50 <= prediction <= upper_50 (approximate, allowing for float precision).
    3. lower_90 <= lower_50 and upper_50 <= upper_90.
    4. variance >= 0.
    5. sample_id is unique.
    6. Methods are one of: "DeepEnsemble", "MCDropout", "SparseGP".
    
    Returns:
        bool: True if integrity checks pass, False otherwise.
    """
    errors = []
    
    # Check for infinite values in numeric columns
    numeric_cols = ["prediction", "variance", "lower_50", "upper_50", "lower_90", "upper_90", "aleatoric", "epistemic", "total"]
    for col in numeric_cols:
        if col in df.columns:
            if np.isinf(df[col]).any():
                errors.append(f"Column '{col}' contains infinite values")
    
    # Check variance non-negativity
    if "variance" in df.columns:
        if (df["variance"] < 0).any():
            errors.append("Variance contains negative values")
    
    # Check interval bounds consistency
    if all(col in df.columns for col in ["lower_50", "prediction", "upper_50"]):
        # Allow small float tolerance
        tol = 1e-9
        if ((df["lower_50"] - df["prediction"]) > tol).any():
            errors.append("lower_50 > prediction in some rows")
        if ((df["prediction"] - df["upper_50"]) > tol).any():
            errors.append("prediction > upper_50 in some rows")
    
    if all(col in df.columns for col in ["lower_90", "lower_50", "upper_50", "upper_90"]):
        if ((df["lower_90"] - df["lower_50"]) > 0).any():
            errors.append("lower_90 > lower_50 in some rows")
        if ((df["upper_50"] - df["upper_90"]) > 0).any():
            errors.append("upper_50 > upper_90 in some rows")
    
    # Check unique sample_id
    if "sample_id" in df.columns:
        if df["sample_id"].duplicated().any():
            errors.append("Duplicate sample_id values found")
    
    # Check valid methods
    valid_methods = {"DeepEnsemble", "MCDropout", "SparseGP"}
    if "method" in df.columns:
        invalid_methods = set(df["method"].unique()) - valid_methods
        if invalid_methods:
            errors.append(f"Invalid method names found: {invalid_methods}")
    
    if errors:
        print(f"Data integrity validation FAILED for {filepath}:")
        for err in errors:
            print(f"  - {err}")
        return False
    
    print(f"Data integrity validation PASSED for {filepath}")
    return True

def main():
    """
    Main entry point for verifying uq_predictions.csv generation and schema compliance.
    """
    # Define paths
    project_root = Path(__file__).resolve().parent.parent.parent
    predictions_path = project_root / "results" / "uq_predictions.csv"
    
    if not predictions_path.exists():
        print(f"ERROR: File not found: {predictions_path}")
        sys.exit(1)
    
    try:
        df = pd.read_csv(predictions_path)
    except Exception as e:
        print(f"ERROR: Failed to read {predictions_path}: {e}")
        sys.exit(1)
    
    print(f"Loaded {predictions_path} with {len(df)} rows and {len(df.columns)} columns")
    print(f"Columns: {list(df.columns)}")
    
    # Run validations
    schema_ok = verify_schema(df, str(predictions_path))
    integrity_ok = verify_data_integrity(df, str(predictions_path))
    
    if schema_ok and integrity_ok:
        print("\n✅ T018 Verification PASSED: results/uq_predictions.csv is valid.")
        sys.exit(0)
    else:
        print("\n❌ T018 Verification FAILED: results/uq_predictions.csv does not meet requirements.")
        sys.exit(1)

if __name__ == "__main__":
    main()
