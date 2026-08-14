"""
T035b: Validate schema of data/processed/model_results.json and data/processed/correlations.csv.

This script performs strict schema validation on the outputs from User Story 2 (Modeling & Correlations).
It verifies:
1. data/processed/model_results.json: Contains required keys (adjusted_r2, rmse, permutation_p_value, 
   bonferroni_corrected_p_values, optimal_lambda, sample_size_mdes, hypothesis_supported).
2. data/processed/correlations.csv: Contains required columns (band, correlation, p_value, 
   bonferroni_corrected_p_value, significant) and valid data types.

Exit Code:
- 0: Validation passed.
- 1: Validation failed (schema mismatch, missing keys, or data integrity issues).
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
from typing import Any, Dict, List, Set

# Import config utilities to resolve paths
# Note: We handle the flexible get_path signature here to avoid import errors if config is broken
try:
    from config import get_path
    # Attempt to resolve paths using the standard signature first
    # If the config module is broken (e.g., get_path signature mismatch), we fallback to hardcoded paths
    # based on the project structure defined in tasks.md.
    try:
        model_results_path = get_path("data/processed/model_results.json")
        correlations_path = get_path("data/processed/correlations.csv")
    except (TypeError, ValueError):
        # Fallback to hardcoded paths if get_path fails
        model_results_path = Path("data/processed/model_results.json")
        correlations_path = Path("data/processed/correlations.csv")
except ImportError:
    model_results_path = Path("data/processed/model_results.json")
    correlations_path = Path("data/processed/correlations.csv")

def validate_model_results_json(path: Path) -> bool:
    """
    Validates the schema of data/processed/model_results.json.
    
    Required Keys:
    - adjusted_r2 (float)
    - rmse (float)
    - permutation_p_value (float)
    - bonferroni_corrected_p_values (dict)
    - optimal_lambda (float, from LASSO)
    - sample_size_mdes (int, from power analysis)
    - hypothesis_supported (bool)
    - model_type (str)
    - cv_folds (int)
    """
    print(f"Validating model results at: {path}")
    
    if not path.exists():
        print(f"ERROR: File not found: {path}")
        return False
    
    try:
        with open(path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {path}: {e}")
        return False
    
    required_keys: Set[str] = {
        "adjusted_r2",
        "rmse",
        "permutation_p_value",
        "bonferroni_corrected_p_values",
        "optimal_lambda",
        "sample_size_mdes",
        "hypothesis_supported",
        "model_type",
        "cv_folds"
    }
    
    missing_keys = required_keys - set(data.keys())
    if missing_keys:
        print(f"ERROR: Missing required keys in model_results.json: {missing_keys}")
        return False
    
    # Type checks
    errors = []
    
    if not isinstance(data["adjusted_r2"], (int, float)):
        errors.append("adjusted_r2 must be numeric")
    if not isinstance(data["rmse"], (int, float)):
        errors.append("rmse must be numeric")
    if not isinstance(data["permutation_p_value"], (int, float)):
        errors.append("permutation_p_value must be numeric")
    if not isinstance(data["optimal_lambda"], (int, float)):
        errors.append("optimal_lambda must be numeric")
    if not isinstance(data["sample_size_mdes"], int):
        errors.append("sample_size_mdes must be an integer")
    if not isinstance(data["hypothesis_supported"], bool):
        errors.append("hypothesis_supported must be a boolean")
    if not isinstance(data["model_type"], str):
        errors.append("model_type must be a string")
    if not isinstance(data["cv_folds"], int):
        errors.append("cv_folds must be an integer")
    if not isinstance(data["bonferroni_corrected_p_values"], dict):
        errors.append("bonferroni_corrected_p_values must be a dictionary")
    else:
        # Check inner keys for bands
        bands = ["delta", "theta", "alpha", "low_beta", "high_beta", "gamma"]
        for band in bands:
            if band not in data["bonferroni_corrected_p_values"]:
                errors.append(f"bonferroni_corrected_p_values missing key: {band}")
            elif not isinstance(data["bonferroni_corrected_p_values"][band], (int, float)):
                errors.append(f"bonferroni_corrected_p_values[{band}] must be numeric")
    
    if errors:
        print("ERROR: Schema validation failed with the following issues:")
        for err in errors:
            print(f"  - {err}")
        return False
    
    print("model_results.json schema validation: PASSED")
    return True

def validate_correlations_csv(path: Path) -> bool:
    """
    Validates the schema of data/processed/correlations.csv.
    
    Required Columns:
    - band (str)
    - correlation (float)
    - p_value (float)
    - bonferroni_corrected_p_value (float)
    - significant (bool)
    
    Constraints:
    - No nulls in required columns
    - 'significant' must be boolean
    - p_values must be between 0 and 1
    """
    print(f"Validating correlations at: {path}")
    
    if not path.exists():
        print(f"ERROR: File not found: {path}")
        return False
    
    try:
        df = pd.read_csv(path)
    except Exception as e:
        print(f"ERROR: Failed to read CSV {path}: {e}")
        return False
    
    required_columns = ["band", "correlation", "p_value", "bonferroni_corrected_p_value", "significant"]
    missing_cols = set(required_columns) - set(df.columns)
    
    if missing_cols:
        print(f"ERROR: Missing required columns in correlations.csv: {missing_cols}")
        return False
    
    # Check for nulls
    null_counts = df[required_columns].isnull().sum()
    if null_counts.any():
        print("ERROR: Null values found in required columns:")
        for col, count in null_counts[null_counts > 0].items():
            print(f"  - {col}: {count} nulls")
        return False
    
    # Type and range checks
    errors = []
    
    # Check 'significant' is boolean
    if not df["significant"].apply(lambda x: isinstance(x, (bool, int)) or str(x).lower() in ['true', 'false', '1', '0']).all():
        errors.append("Column 'significant' contains non-boolean values")
    
    # Check p-values are in [0, 1]
    if not (df["p_value"] >= 0).all() or not (df["p_value"] <= 1).all():
        errors.append("p_value must be between 0 and 1")
    if not (df["bonferroni_corrected_p_value"] >= 0).all() or not (df["bonferroni_corrected_p_value"] <= 1).all():
        errors.append("bonferroni_corrected_p_value must be between 0 and 1")
    
    # Check correlation range [-1, 1]
    if not (df["correlation"] >= -1).all() or not (df["correlation"] <= 1).all():
        errors.append("correlation must be between -1 and 1")
    
    # Check bands are valid
    valid_bands = {"delta", "theta", "alpha", "low_beta", "high_beta", "gamma"}
    invalid_bands = set(df["band"].unique()) - valid_bands
    if invalid_bands:
        errors.append(f"Invalid band names found: {invalid_bands}")
    
    if errors:
        print("ERROR: Correlations validation failed with the following issues:")
        for err in errors:
            print(f"  - {err}")
        return False
    
    print("correlations.csv schema validation: PASSED")
    return True

def main():
    print("Starting T035b: Schema Validation for Model Results and Correlations")
    print("-" * 60)
    
    results_valid = validate_model_results_json(model_results_path)
    print("-" * 60)
    correlations_valid = validate_correlations_csv(correlations_path)
    print("-" * 60)
    
    if results_valid and correlations_valid:
        print("T035b: ALL VALIDATIONS PASSED")
        sys.exit(0)
    else:
        print("T035b: VALIDATION FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
