"""
Contract tests for the CLUTRR dataset schema.

These tests verify that the downloaded CLUTRR dataset adheres to the expected
schema (columns, data types) required for downstream processing.
"""
import os
import pytest
import pandas as pd
from pathlib import Path

# Project root path setup
_project_root = Path(__file__).resolve().parent.parent.parent
CLUTRR_PATH = _project_root / "data" / "raw" / "clutrr.parquet"

# Expected schema definition
# CLUTRR typically contains: story, family_tree, question, answer, etc.
# We define a flexible but strict schema check for the presence of key columns.
EXPECTED_COLUMNS = {
    "story",
    "family_tree",
    "question",
    "answer",
}

def test_clutrr_file_exists():
    """Asserts that the CLUTRR parquet file exists on disk."""
    assert CLUTRR_PATH.exists(), f"CLUTRR dataset file not found at {CLUTRR_PATH}"

def test_clutrr_schema():
    """
    Asserts that the CLUTRR dataset contains the required columns.
    
    This is a contract test ensuring the data ingestion (T006) produced
    a valid dataset structure.
    """
    test_clutrr_file_exists()
    
    df = pd.read_parquet(CLUTRR_PATH)
    
    assert isinstance(df, pd.DataFrame), "Loaded data is not a DataFrame"
    assert len(df) > 0, "Dataset is empty"
    
    # Check for required columns
    missing_columns = EXPECTED_COLUMNS - set(df.columns)
    assert not missing_columns, f"Missing required columns: {missing_columns}"

def test_clutrr_data_types():
    """
    Asserts that the required columns are of string type (or object).
    
    CLUTRR data is textual; numeric fields (if any) should also be validated
    if they exist, but the core contract is text-based reasoning.
    """
    test_clutrr_file_exists()
    
    df = pd.read_parquet(CLUTRR_PATH)
    
    text_columns = ["story", "family_tree", "question", "answer"]
    for col in text_columns:
        if col in df.columns:
            # Check if the column is of object/string type
            # Allow for potential NaNs, so we check non-null values
            non_null = df[col].dropna()
            if len(non_null) > 0:
                # Check if the first non-null value is a string
                assert isinstance(non_null.iloc[0], str), f"Column '{col}' contains non-string values"
