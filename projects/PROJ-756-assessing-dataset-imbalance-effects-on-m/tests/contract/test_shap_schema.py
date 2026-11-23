"""
Contract test for SHAP output schema (T034).
Validates the schema of rank_shift.csv produced by T038.
"""
import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add code directory to path if needed, though usually tests run from root
CODE_DIR = Path(__file__).parent.parent.parent / "code"
RESULTS_DIR = Path(__file__).parent.parent.parent / "results"
SHAP_RESULTS_DIR = RESULTS_DIR / "shap_analysis"

# Expected schema definition
EXPECTED_COLUMNS = ["feature", "rank_skewed", "rank_balanced", "rank_shift"]
REQUIRED_TYPES = {
    "feature": str,
    "rank_skewed": (int, float),
    "rank_balanced": (int, float),
    "rank_shift": (int, float)
}

class SHAPSchemaError(Exception):
    """Raised when SHAP output schema validation fails."""
    pass

def test_shap_rank_shift_schema_exists():
    """Verify that the rank_shift.csv file exists."""
    file_path = SHAP_RESULTS_DIR / "rank_shift.csv"
    assert file_path.exists(), f"Contract test failed: {file_path} does not exist. " \
                               "Ensure T038 (shap_ranking.py) has been executed successfully."

def test_shap_rank_shift_schema_columns():
    """Verify that rank_shift.csv contains the required columns."""
    file_path = SHAP_RESULTS_DIR / "rank_shift.csv"
    
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise SHAPSchemaError(f"Failed to read {file_path}: {e}")

    missing_cols = set(EXPECTED_COLUMNS) - set(df.columns)
    extra_cols = set(df.columns) - set(EXPECTED_COLUMNS)
    
    assert not missing_cols, f"Contract test failed: Missing required columns: {missing_cols}. " \
                             f"Found columns: {list(df.columns)}. Expected: {EXPECTED_COLUMNS}"
    
    if extra_cols:
        # Log warning but do not fail if extra columns are present, 
        # as long as required ones exist. 
        # However, strict schema validation often fails on extra cols. 
        # Based on task description "validates rank-shift CSV schema", we ensure exact match or superset.
        # Let's be strict: only allowed columns are expected.
        assert not extra_cols, f"Contract test failed: Unexpected columns found: {extra_cols}. " \
                               f"Only {EXPECTED_COLUMNS} are allowed."

def test_shap_rank_shift_schema_types():
    """Verify that columns in rank_shift.csv have the expected data types."""
    file_path = SHAP_RESULTS_DIR / "rank_shift.csv"
    
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise SHAPSchemaError(f"Failed to read {file_path}: {e}")

    # Ensure at least one row exists to check types
    assert len(df) > 0, "Contract test failed: rank_shift.csv is empty. " \
                        "Ensure T038 generated data."

    for col, expected_type in REQUIRED_TYPES.items():
        if col not in df.columns:
            continue # Already handled in column check
        
        actual_type = df[col].dtype
        
        # Check if actual type is compatible with expected type
        # For numeric columns, pandas might infer int64, float64, etc.
        if isinstance(expected_type, tuple):
            # Allow any of the tuple types
            is_valid = any(
                pd.api.types.is_dtype_equal(actual_type, t) or 
                (isinstance(expected_type, type) and issubclass(actual_type.type, expected_type))
                for t in expected_type
            )
            # Special handling for numeric: allow int/float interchangeability if values are whole numbers
            if not is_valid and col != "feature":
                # Check if numeric conversion is possible and valid
                try:
                    pd.to_numeric(df[col])
                    is_valid = True # If it converts, it's acceptable for numeric fields
                except (ValueError, TypeError):
                    is_valid = False
        else:
            is_valid = pd.api.types.is_dtype_equal(actual_type, expected_type)
        
        assert is_valid, f"Contract test failed: Column '{col}' has type {actual_type}, " \
                         f"expected {expected_type}."

def test_shap_rank_shift_schema_values():
    """Verify that values in rank_shift.csv are logically valid."""
    file_path = SHAP_RESULTS_DIR / "rank_shift.csv"
    
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise SHAPSchemaError(f"Failed to read {file_path}: {e}")

    # Check for non-null values in critical columns
    null_counts = df[EXPECTED_COLUMNS].isnull().sum()
    assert null_counts.sum() == 0, f"Contract test failed: Null values found in required columns:\n{null_counts}"

    # Check that rank values are non-negative integers (or floats representing integers)
    rank_cols = ["rank_skewed", "rank_balanced"]
    for col in rank_cols:
        if col in df.columns:
            # Ensure ranks are >= 0
            assert (df[col] >= 0).all(), f"Contract test failed: Negative rank values found in '{col}'."
            # Ensure ranks are integers (or close to integers)
            # Allow small floating point errors if converted
            assert (df[col] == df[col].round()).all(), f"Contract test failed: Non-integer rank values found in '{col}'."

    # Check that rank_shift is consistent (rank_skewed - rank_balanced)
    if "rank_shift" in df.columns and "rank_skewed" in df.columns and "rank_balanced" in df.columns:
        calculated_shift = df["rank_skewed"] - df["rank_balanced"]
        assert (df["rank_shift"] == calculated_shift).all(), \
            "Contract test failed: 'rank_shift' column does not match 'rank_skewed' - 'rank_balanced'."

if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])