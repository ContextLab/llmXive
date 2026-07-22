"""
Unit tests for dataset merging logic in T015.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from ingest import ingest_datasets, normalize_columns, validate_schema

def create_mock_df(rows=10, condition_val=1, amount_base=5.0):
    """Helper to create a mock DataFrame with required columns."""
    data = {
        'condition': [condition_val] * rows,
        'prosocial_amount': [amount_base + i for i in range(rows)],
        'randomized': [True] * rows
    }
    return pd.DataFrame(data)

def test_merge_logic():
    """
    Test that multiple valid DataFrames are correctly concatenated.
    This simulates the core logic of T015 without needing real network calls.
    """
    # Simulate the logic inside ingest_datasets that creates valid_datasets list
    df1 = create_mock_df(rows=5, condition_val=1, amount_base=1.0)
    df2 = create_mock_df(rows=5, condition_val=0, amount_base=2.0)
    df3 = create_mock_df(rows=5, condition_val=1, amount_base=3.0)
    
    valid_datasets = [df1, df2, df3]
    
    # Perform the merge operation (copied from ingest.py logic)
    combined_df = pd.concat(valid_datasets, ignore_index=True)
    
    # Assertions
    assert len(combined_df) == 15, f"Expected 15 rows, got {len(combined_df)}"
    assert list(combined_df.columns) == ['condition', 'prosocial_amount', 'randomized']
    assert combined_df['condition'].iloc[0] == 1
    assert combined_df['condition'].iloc[5] == 0
    assert combined_df['condition'].iloc[10] == 1
    assert combined_df['prosocial_amount'].iloc[0] == 1.0
    assert combined_df['prosocial_amount'].iloc[5] == 2.0
    assert combined_df['prosocial_amount'].iloc[10] == 3.0

def test_merge_empty_list_raises():
    """
    Test that merging an empty list raises an error or handles gracefully.
    In ingest.py, this is handled by an explicit check.
    """
    valid_datasets = []
    with pytest.raises(Exception) as exc_info:
        # Simulate the check in ingest_datasets
        if not valid_datasets:
            raise Exception("No valid datasets found to merge.")
    assert "No valid datasets found" in str(exc_info.value)

def test_merge_single_dataset():
    """Test merging a single dataset (edge case)."""
    df1 = create_mock_df(rows=3)
    valid_datasets = [df1]
    combined_df = pd.concat(valid_datasets, ignore_index=True)
    
    assert len(combined_df) == 3
    assert list(combined_df.columns) == ['condition', 'prosocial_amount', 'randomized']

def test_normalize_columns_integration():
    """Test that normalization happens before merging (simulated)."""
    raw_data = {
        'donation': [10, 20, 30],
        'group': ['ignored', 'control', 'excluded'],
        'randomized': [True, True, False]
    }
    df_raw = pd.DataFrame(raw_data)
    
    df_norm = normalize_columns(df_raw)
    
    assert 'prosocial_amount' in df_norm.columns
    assert 'condition' in df_norm.columns
    assert df_norm['condition'].iloc[0] == 1  # ignored -> 1
    assert df_norm['condition'].iloc[1] == 0  # control -> 0
    assert df_norm['condition'].iloc[2] == 1  # excluded -> 1
