import pytest
import pandas as pd
import numpy as np
import os
from pathlib import Path

# Import the function to test
# Assuming ingestion.py is in the code directory
import sys
sys.path.insert(0, 'code')
from ingestion import handle_duplicates

def test_handle_duplicates_aggregation():
    """Test that duplicates are aggregated using mean."""
    data = {
        'smiles': ['CCO', 'CCO', 'CCO', 'CC', 'CC'],
        'target': [1.0, 2.0, 3.0, 10.0, 20.0],
        'source_id': ['A', 'B', 'C', 'D', 'E']
    }
    df = pd.DataFrame(data)
    
    result = handle_duplicates(df)
    
    # Check shape
    assert len(result) == 2, "Should have 2 unique SMILES"
    
    # Check aggregation for 'CCO'
    cco_row = result[result['smiles'] == 'CCO'].iloc[0]
    assert cco_row['target_mean'] == 2.0, "Mean of 1, 2, 3 should be 2.0"
    assert cco_row['count'] == 3, "Count should be 3"
    
    # Check aggregation for 'CC'
    cc_row = result[result['smiles'] == 'CC'].iloc[0]
    assert cc_row['target_mean'] == 15.0, "Mean of 10, 20 should be 15.0"
    assert cc_row['count'] == 2, "Count should be 2"
    
    # Check schema
    expected_cols = ['smiles', 'target_mean', 'count', 'source_id']
    assert list(result.columns) == expected_cols, f"Schema mismatch: {list(result.columns)}"

def test_handle_duplicates_missing_target():
    """Test that rows with missing targets are excluded."""
    data = {
        'smiles': ['CCO', 'CCO', 'CC'],
        'target': [1.0, np.nan, 10.0],
        'source_id': ['A', 'B', 'C']
    }
    df = pd.DataFrame(data)
    
    result = handle_duplicates(df)
    
    # 'CCO' should only have one valid entry (1.0)
    cco_row = result[result['smiles'] == 'CCO'].iloc[0]
    assert cco_row['target_mean'] == 1.0
    assert cco_row['count'] == 1

def test_handle_duplicates_empty_df():
    """Test that empty DataFrame raises error."""
    df = pd.DataFrame(columns=['smiles', 'target'])
    with pytest.raises(ValueError):
        handle_duplicates(df)

def test_handle_duplicates_output_file():
    """Test that the output file is created."""
    data = {
        'smiles': ['CCO'],
        'target': [1.0],
        'source_id': ['A']
    }
    df = pd.DataFrame(data)
    
    # Ensure directory exists for test
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    
    result = handle_duplicates(df)
    
    assert Path("data/processed/deduplicated.csv").exists()
