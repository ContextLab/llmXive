"""
Unit tests for code/modeling/filter.py (T034).
"""
import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Adjust import based on project structure
# Assuming tests are run with PYTHONPATH set to project root
from modeling.filter import load_pre_filter_dataset, filter_samples, write_filtered_dataset

@pytest.fixture
def sample_pre_filter_data():
    """
    Creates a temporary CSV file simulating T014c output.
    """
    data = {
        'sample_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
        'Pb_map_path': ['p1', 'p2', 'p3', 'p4', 'p5'],
        'PCE': [15.0, 16.0, 17.0, 18.0, 19.0],
        'validation_flag': [0, 1, 0, 0, 0],  # S2 failed validation
        'depth_flag': [0, 0, 1, 0, 0]         # S3 failed depth check
    }
    return data

@pytest.fixture
def temp_input_file(sample_pre_filter_data):
    """
    Creates a temporary input file for testing.
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df = pd.DataFrame(sample_pre_filter_data)
        df.to_csv(f, index=False)
        return f.name

@pytest.fixture
def temp_output_dir():
    """
    Creates a temporary directory for output files.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_load_pre_filter_dataset(temp_input_file):
    """Test loading the pre-filter dataset."""
    df = load_pre_filter_dataset(temp_input_file)
    assert len(df) == 5
    assert 'sample_id' in df.columns
    assert 'validation_flag' in df.columns
    assert 'depth_flag' in df.columns

def test_filter_samples_logic(temp_input_file):
    """
    Test that filter_samples correctly removes rows with non-zero flags.
    Expected: S1 (0,0) kept. S2 (1,0) dropped. S3 (0,1) dropped. S4 (0,0) kept. S5 (0,0) kept.
    Result: 3 rows kept.
    """
    df = load_pre_filter_dataset(temp_input_file)
    filtered_df, kept, dropped_val, dropped_dep = filter_samples(df)
    
    assert kept == 3
    assert dropped_val == 1  # S2
    assert dropped_dep == 1  # S3
    
    # Verify specific IDs
    kept_ids = set(filtered_df['sample_id'].tolist())
    assert kept_ids == {'S1', 'S4', 'S5'}
    
    # Verify dropped IDs are not present
    assert 'S2' not in kept_ids
    assert 'S3' not in kept_ids

def test_write_filtered_dataset(temp_input_file, temp_output_dir):
    """Test writing the filtered dataset."""
    df = load_pre_filter_dataset(temp_input_file)
    filtered_df, _, _, _ = filter_samples(df)
    
    output_path = os.path.join(temp_output_dir, 'primary_analysis_dataset.csv')
    write_filtered_dataset(filtered_df, output_path)
    
    assert os.path.exists(output_path)
    
    # Verify content
    result_df = pd.read_csv(output_path)
    assert len(result_df) == 3
    assert list(result_df['sample_id']) == ['S1', 'S4', 'S5']

def test_missing_columns(temp_input_file, sample_pre_filter_data):
    """Test that missing required columns raise an error."""
    # Modify data to remove a required column
    bad_data = {k: v for k, v in sample_pre_filter_data.items() if k != 'validation_flag'}
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        pd.DataFrame(bad_data).to_csv(f, index=False)
        bad_path = f.name
    
    with pytest.raises(ValueError, match="Missing required columns"):
        load_pre_filter_dataset(bad_path)
    
    os.unlink(bad_path)