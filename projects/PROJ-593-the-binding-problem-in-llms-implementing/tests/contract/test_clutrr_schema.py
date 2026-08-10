"""
Contract tests for the CLUTRR dataset schema.

These tests verify that the downloaded CLUTRR dataset matches the expected
schema and data types.
"""
import os
import pytest
import pandas as pd
from pathlib import Path


# Path to the expected data file
DATA_FILE_PATH = Path("data/raw/clutrr.parquet")


def test_clutrr_file_exists():
    """Verify that the CLUTRR parquet file exists."""
    assert DATA_FILE_PATH.exists(), f"CLUTRR dataset file not found at {DATA_FILE_PATH}"


def test_clutrr_schema():
    """
    Verify that the CLUTRR dataset has the expected columns.
    
    The CLUTRR dataset from tasksource/clutrr typically contains columns such as:
    - story: The narrative text
    - query: The question to answer
    - answer: The correct answer
    - family_tree: The underlying family structure
    - family_members: List of family members
    - num_hops: Number of reasoning hops required
    """
    df = pd.read_parquet(DATA_FILE_PATH)
    
    # Define expected columns based on the tasksource/clutrr dataset
    # Note: Exact columns may vary slightly, but these are the core ones
    expected_columns = {
        'story', 
        'query', 
        'answer', 
        'family_tree', 
        'family_members', 
        'num_hops'
    }
    
    actual_columns = set(df.columns)
    
    # Check that all expected columns are present
    missing_columns = expected_columns - actual_columns
    assert not missing_columns, f"Missing expected columns in CLUTRR dataset: {missing_columns}"


def test_clutrr_data_types():
    """
    Verify that the data types in the CLUTRR dataset are as expected.
    """
    df = pd.read_parquet(DATA_FILE_PATH)
    
    # Check that required columns exist first
    required_columns = ['story', 'query', 'answer', 'num_hops']
    for col in required_columns:
        assert col in df.columns, f"Required column '{col}' missing from dataset"
    
    # Verify data types
    # 'story', 'query', 'answer' should be strings
    assert df['story'].dtype == 'object', "Column 'story' should be of string/object type"
    assert df['query'].dtype == 'object', "Column 'query' should be of string/object type"
    assert df['answer'].dtype == 'object', "Column 'answer' should be of string/object type"
    
    # 'num_hops' should be an integer
    assert pd.api.types.is_integer_dtype(df['num_hops']), "Column 'num_hops' should be of integer type"
    
    # Verify that 'story' and 'query' are not empty
    assert df['story'].str.len().min() > 0, "Some 'story' entries are empty"
    assert df['query'].str.len().min() > 0, "Some 'query' entries are empty"
    
    # Verify that 'answer' is not empty
    assert df['answer'].str.len().min() > 0, "Some 'answer' entries are empty"
    
    # Verify that 'num_hops' is positive
    assert (df['num_hops'] > 0).all(), "All 'num_hops' values should be positive"
