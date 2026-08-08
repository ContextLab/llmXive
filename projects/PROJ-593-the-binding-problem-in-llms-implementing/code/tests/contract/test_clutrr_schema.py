import os
import pytest
import pandas as pd
from pathlib import Path

DATA_PATH = Path("data/raw/clutrr.parquet")

def test_clutrr_file_exists():
    """Verify that the CLUTRR data file exists."""
    assert DATA_PATH.exists(), f"CLUTRR data file not found at {DATA_PATH}"

def test_clutrr_schema():
    """Verify the CLUTRR dataset has the expected columns."""
    assert DATA_PATH.exists(), f"CLUTRR data file not found at {DATA_PATH}"
    
    df = pd.read_parquet(DATA_PATH)
    
    # CLUTRR dataset typically contains columns like:
    # 'story', 'question', 'answer', 'family_tree', etc.
    # We check for the most critical columns for reasoning tasks.
    required_columns = ['story', 'question', 'answer']
    
    for col in required_columns:
        assert col in df.columns, f"Missing required column: {col}"
    
    # Verify data types
    assert df['story'].dtype == 'object', "Column 'story' should be string/object"
    assert df['question'].dtype == 'object', "Column 'question' should be string/object"
    assert df['answer'].dtype == 'object', "Column 'answer' should be string/object"

def test_clutrr_data_types():
    """Verify the CLUTRR dataset contains non-empty data."""
    assert DATA_PATH.exists(), f"CLUTRR data file not found at {DATA_PATH}"
    
    df = pd.read_parquet(DATA_PATH)
    
    # Check that we have data
    assert len(df) > 0, "CLUTRR dataset is empty"
    
    # Check that story, question, and answer fields are not empty strings
    assert not df['story'].isna().all(), "All 'story' values are NA"
    assert not df['question'].isna().all(), "All 'question' values are NA"
    assert not df['answer'].isna().all(), "All 'answer' values are NA"
    
    # Check for reasonable length (stories should have some content)
    assert df['story'].str.len().mean() > 0, "Stories appear to be empty"
    assert df['question'].str.len().mean() > 0, "Questions appear to be empty"
    assert df['answer'].str.len().mean() > 0, "Answers appear to be empty"
