import pandas as pd
import pytest
import tempfile
import os
from pathlib import Path
from code.utils.deduplicator import handle_duplicates

def test_handle_duplicates_basic():
    """Test basic duplicate handling with mean aggregation."""
    data = {
        'smiles': ['CCO', 'CCO', 'CCO', 'C1=CC=CC=C1', 'C1=CC=CC=C1'],
        'target': [1.0, 2.0, 3.0, 4.0, 6.0],
        'source_id': ['nist', 'nist', 'pubchem', 'mtr', 'mtr']
    }
    df = pd.DataFrame(data)
    
    result = handle_duplicates(df)
    
    # Check structure
    assert 'smiles' in result.columns
    assert 'target_mean' in result.columns
    assert 'count' in result.columns
    assert 'source_id' in result.columns
    
    # Check values for CCO (mean of 1, 2, 3 = 2.0)
    cco_row = result[result['smiles'] == 'CCO'].iloc[0]
    assert abs(cco_row['target_mean'] - 2.0) < 1e-6
    assert cco_row['count'] == 3
    
    # Check values for Benzene (mean of 4, 6 = 5.0)
    benz_row = result[result['smiles'] == 'C1=CC=CC=C1'].iloc[0]
    assert abs(benz_row['target_mean'] - 5.0) < 1e-6
    assert benz_row['count'] == 2

def test_handle_duplicates_missing_source_id():
    """Test handling when source_id column is missing."""
    data = {
        'smiles': ['CCO', 'CCO'],
        'target': [1.0, 2.0]
    }
    df = pd.DataFrame(data)
    
    # Should not raise, should fill with 'unknown'
    result = handle_duplicates(df)
    
    assert 'source_id' in result.columns
    assert result['source_id'].iloc[0] == 'unknown'

def test_handle_duplicates_empty_df():
    """Test handling of empty DataFrame."""
    df = pd.DataFrame(columns=['smiles', 'target'])
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'out.csv')
        result = handle_duplicates(df, output_path)
        
        assert result.empty
        assert os.path.exists(output_path)

def test_handle_duplicates_save_to_file():
    """Test that results are saved correctly to file."""
    data = {
        'smiles': ['CCO', 'CCO'],
        'target': [10.0, 20.0],
        'source_id': ['nist', 'nist']
    }
    df = pd.DataFrame(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'dedup.csv')
        handle_duplicates(df, output_path)
        
        assert os.path.exists(output_path)
        saved_df = pd.read_csv(output_path)
        assert len(saved_df) == 1
        assert abs(saved_df['target_mean'].iloc[0] - 15.0) < 1e-6