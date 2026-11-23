"""
Unit tests for Task T014a: Generate Cleaned Dataset
"""

import os
import json
import tempfile
import pandas as pd
from pathlib import Path
import pytest

# Import the module functions
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from task_t014a_create_cleaned_dataset import (
    create_cleaned_dataset,
    load_intermediate_dataset,
    save_cleaned_dataset,
    get_config_paths
)

@pytest.fixture
def sample_df():
    """Create a sample DataFrame mimicking cleaned_dataset.csv"""
    return pd.DataFrame({
        'participant_id': ['P001', 'P002', 'P003'],
        'stimulus_type': ['nostalgia', 'control', 'nostalgia'],
        'perseverative_errors': [12.0, 15.0, 10.0],
        'categories_completed': [5.0, 4.0, 6.0],
        'age': [70, 68, 72],
        'extra_col': ['a', 'b', 'c']  # Should be dropped
    })

@pytest.fixture
def temp_dir():
    """Create a temporary directory for file I/O tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_create_cleaned_dataset_selection(sample_df):
    """Test that only required columns are selected"""
    required_cols = ['participant_id', 'stimulus_type', 'perseverative_errors', 'categories_completed', 'age']
    result = create_cleaned_dataset(sample_df, required_cols)
    
    assert list(result.columns) == required_cols
    assert len(result) == len(sample_df)
    assert 'extra_col' not in result.columns

def test_create_cleaned_dataset_missing_column(sample_df):
    """Test error handling when a required column is missing"""
    required_cols = ['participant_id', 'stimulus_type', 'missing_col', 'age']
    
    with pytest.raises(ValueError) as excinfo:
        create_cleaned_dataset(sample_df, required_cols)
    
    assert "Missing required columns" in str(excinfo.value)
    assert "missing_col" in str(excinfo.value)

def test_save_and_load_cleaned_dataset(sample_df, temp_dir):
    """Test saving to CSV and loading it back"""
    output_path = temp_dir / "test_output.csv"
    
    # Save
    save_cleaned_dataset(sample_df, output_path)
    
    # Verify file exists
    assert output_path.exists()
    
    # Load back
    loaded_df = pd.read_csv(output_path)
    
    # Verify content matches (order might differ if not sorted, but content should)
    assert list(loaded_df.columns) == list(sample_df.columns)
    assert len(loaded_df) == len(sample_df)
    pd.testing.assert_frame_equal(loaded_df, sample_df)

def test_load_intermediate_dataset_missing_file(temp_dir):
    """Test error handling when input file is missing"""
    # Create a fake paths dict pointing to a non-existent file
    paths = {
        "input_path": temp_dir / "non_existent.csv"
    }
    
    with pytest.raises(FileNotFoundError):
        load_intermediate_dataset(paths)

def test_numeric_conversion(sample_df, temp_dir):
    """Test that numeric columns are properly handled"""
    # Introduce a string in a numeric column to test coercion
    sample_df.loc[0, 'age'] = '70' 
    sample_df.loc[0, 'perseverative_errors'] = '12.5'
    
    required_cols = ['participant_id', 'stimulus_type', 'perseverative_errors', 'categories_completed', 'age']
    result = create_cleaned_dataset(sample_df, required_cols)
    
    # Check types
    assert pd.api.types.is_numeric_dtype(result['age'])
    assert pd.api.types.is_numeric_dtype(result['perseverative_errors'])