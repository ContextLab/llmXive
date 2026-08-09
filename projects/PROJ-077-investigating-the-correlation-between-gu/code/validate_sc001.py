"""
Validation script for Success Criteria SC-001.

Reads `data/processed/correlation_results.csv` and verifies:
1. The `r_value` column contains valid float values.
2. The `p_value` column contains valid float values.
3. The p-value is less than 0.05 (statistical significance threshold).

This script validates the Plan-corrected Raw Shannon Index analysis
against Spec Override T046 (replacing SC-001).

Exit codes:
0: Validation passed (results are significant).
1: Validation failed (results not significant, missing data, or file error).
"""

import os
import sys
import pandas as pd
from pathlib import Path

# Project root is the parent of the code directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CORRELATION_RESULTS_PATH = PROJECT_ROOT / "data" / "processed" / "correlation_results.csv"

def validate_sc001() -> bool:
    """
    Validates the correlation results against SC-001.

    Returns:
        bool: True if validation passes, False otherwise.
    """
    if not CORRELATION_RESULTS_PATH.exists():
        print(f"ERROR: Correlation results file not found at {CORRELATION_RESULTS_PATH}")
        print("HINT: Run the analysis pipeline (code/analysis.py) first to generate this file.")
        return False

    try:
        df = pd.read_csv(CORRELATION_RESULTS_PATH)
    except Exception as e:
        print(f"ERROR: Failed to read correlation results CSV: {e}")
        return False

    if df.empty:
        print("ERROR: Correlation results file is empty.")
        return False

    required_columns = ['r_value', 'p_value', 'n_obs']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        print(f"ERROR: Missing required columns in {CORRELATION_RESULTS_PATH}: {missing_cols}")
        return False

    # Check for valid float types and non-null values
    try:
        df['r_value'] = pd.to_numeric(df['r_value'], errors='raise')
        df['p_value'] = pd.to_numeric(df['p_value'], errors='raise')
    except (ValueError, TypeError) as e:
        print(f"ERROR: Non-numeric values found in r_value or p_value columns: {e}")
        return False

    if df['r_value'].isnull().any() or df['p_value'].isnull().any():
        print("ERROR: Null values found in r_value or p_value columns.")
        return False

    # SC-001 Validation: p_value < 0.05
    # If multiple rows exist, we typically expect at least one significant finding
    # or we check the primary comparison. Assuming the first row is the primary result.
    primary_p_value = df.iloc[0]['p_value']
    primary_r_value = df.iloc[0]['r_value']

    threshold = 0.05
    is_significant = primary_p_value < threshold

    print(f"Validation Report for SC-001:")
    print(f"  File: {CORRELATION_RESULTS_PATH}")
    print(f"  Rows found: {len(df)}")
    print(f"  Primary r_value: {primary_r_value:.4f}")
    print(f"  Primary p_value: {primary_p_value:.6f}")
    print(f"  Threshold (alpha): {threshold}")

    if is_significant:
        print("  STATUS: PASS - p-value < 0.05 (Significant association detected).")
        return True
    else:
        print("  STATUS: FAIL - p-value >= 0.05 (No significant association detected).")
        return False

def main():
    success = validate_sc001()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()