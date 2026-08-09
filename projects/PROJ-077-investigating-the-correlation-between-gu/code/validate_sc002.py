"""
Validation script for Success Criteria 002 (SC-002).

Validates the regression results to ensure:
1. The 'coefficient' column contains valid float values.
2. The 'p-value' for the Shannon predictor is < 0.05.

This validates the Plan-corrected Raw Shannon regression against Spec Override T046.
"""
import os
import sys
import pandas as pd
from pathlib import Path

# Project root is assumed to be the parent of 'code'
PROJECT_ROOT = Path(__file__).resolve().parent.parent
REGRESSION_RESULTS_PATH = PROJECT_ROOT / "data" / "processed" / "regression_results.csv"

def validate_sc002(input_path: Path) -> bool:
    """
    Validates SC-002:
    - Reads regression_results.csv
    - Verifies 'coefficient' is a float
    - Verifies 'p-value' < 0.05 for the Shannon predictor row.
    
    Args:
        input_path: Path to regression_results.csv
        
    Returns:
        bool: True if validation passes, False otherwise.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If required columns are missing or data types are invalid.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Regression results file not found: {input_path}")
        
    df = pd.read_csv(input_path)
    
    # Check required columns
    required_cols = ['predictor', 'coefficient', 'p-value']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {input_path}: {missing_cols}")
        
    # Identify the Shannon predictor row
    # The predictor column should contain the name of the Shannon index variable
    shannon_rows = df[df['predictor'].str.contains('shannon', case=False, na=False)]
    
    if shannon_rows.empty:
        raise ValueError(f"No rows found for 'shannon' predictor in {input_path}")
        
    # Validate coefficient is float
    # Pandas usually reads numbers as float, but we explicitly check for NaN or non-numeric
    try:
        shannon_coeff = shannon_rows['coefficient'].iloc[0]
        float(shannon_coeff)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid coefficient value for Shannon predictor: {shannon_coeff}")
        
    # Validate p-value < 0.05
    p_val = shannon_rows['p-value'].iloc[0]
    try:
        p_val_float = float(p_val)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid p-value for Shannon predictor: {p_val}")
        
    if p_val_float >= 0.05:
        print(f"SC-002 VALIDATION FAILED: p-value ({p_val_float}) is not < 0.05")
        return False
        
    print(f"SC-002 VALIDATION PASSED: Shannon predictor coefficient={shannon_coeff}, p-value={p_val_float}")
    return True

def main():
    """Entry point for validation."""
    try:
        if validate_sc002(REGRESSION_RESULTS_PATH):
            print("Validation successful.")
            sys.exit(0)
        else:
            print("Validation failed.")
            sys.exit(1)
    except Exception as e:
        print(f"Validation error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()