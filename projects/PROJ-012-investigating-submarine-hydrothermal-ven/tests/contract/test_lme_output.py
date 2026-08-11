"""
Contract test for LME output schema (T016).

This test verifies that the Linear Mixed-Effects (LME) analysis results
written to `data/processed/lme_results.csv` conform to the required schema
defined in the project specifications.

Required columns (per FR-003.1 and US2 implementation):
- estimate: float (regression coefficient)
- se: float (standard error)
- p_value: float (p-value)
- model_type: str (e.g., "LME", "OLS", "Spearman")

The test fails if the file is missing, empty, or contains incorrect columns.
"""

import os
import pandas as pd
import pytest
from pathlib import Path

# Expected schema definition
REQUIRED_COLUMNS = {"estimate", "se", "p_value", "model_type"}
OUTPUT_PATH = Path("data/processed/lme_results.csv")

def test_lme_output_schema_exists():
    """Verify the LME results file exists."""
    assert OUTPUT_PATH.exists(), f"Output file {OUTPUT_PATH} not found. Run the analysis pipeline first."

def test_lme_output_schema_columns():
    """Verify the LME results file contains all required columns."""
    df = pd.read_csv(OUTPUT_PATH)
    
    # Check column set
    missing_cols = REQUIRED_COLUMNS - set(df.columns)
    assert not missing_cols, f"Missing required columns in {OUTPUT_PATH}: {missing_cols}"
    
    # Check for unexpected columns (optional strictness, but good for contracts)
    extra_cols = set(df.columns) - REQUIRED_COLUMNS
    # We allow extra metadata columns if needed, but the core 4 must exist.
    # If the spec demands *only* these, uncomment the next line:
    # assert not extra_cols, f"Unexpected columns found: {extra_cols}"

def test_lme_output_schema_types():
    """Verify data types of core numeric columns."""
    df = pd.read_csv(OUTPUT_PATH)
    
    # Check numeric types
    numeric_cols = ["estimate", "se", "p_value"]
    for col in numeric_cols:
        assert pd.api.types.is_numeric_dtype(df[col]), f"Column '{col}' must be numeric, got {df[col].dtype}"
    
    # Check model_type is string/object
    assert df["model_type"].dtype == object or pd.api.types.is_string_dtype(df["model_type"]), \
        "Column 'model_type' must be string-like"

def test_lme_output_schema_values():
    """Verify logical constraints on values (e.g., p_value between 0 and 1)."""
    df = pd.read_csv(OUTPUT_PATH)
    
    # p_value constraint
    if len(df) > 0:
        assert (df["p_value"] >= 0).all() and (df["p_value"] <= 1).all(), \
            "p_value must be between 0 and 1"
        
        # se should be non-negative
        assert (df["se"] >= 0).all(), "Standard error (se) must be non-negative"

def test_lme_output_has_data():
    """Verify the file is not empty (has at least one row)."""
    df = pd.read_csv(OUTPUT_PATH)
    assert len(df) > 0, f"Output file {OUTPUT_PATH} is empty. Analysis did not produce results."