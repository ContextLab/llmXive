"""
Unit tests for descriptor computation module.
Tests specifically for Magpie descriptor computation and L2-normalization.
"""
import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from descriptors import load_raw_data, compute_descriptors, save_descriptors

@pytest.fixture
def sample_preprocessed_data():
    """Create a temporary preprocessed data file for testing."""
    data = {
        'formula': ['H2O', 'NaCl', 'SiO2', 'Fe2O3', 'CH4'],
        'target_property': [1.0, 2.0, 3.0, 4.0, 5.0]
    }
    df = pd.DataFrame(data)
    
    # Create a temporary directory and file
    temp_dir = tempfile.mkdtemp()
    temp_file = Path(temp_dir) / "preprocessed_data.parquet"
    df.to_parquet(temp_file)
    
    return temp_file

def test_compute_descriptors_l2_normalization(sample_preprocessed_data):
    """Test that compute_descriptors correctly computes and L2-normalizes descriptors."""
    # Temporarily override INPUT_FILE for the test
    import descriptors
    original_input = descriptors.INPUT_FILE
    descriptors.INPUT_FILE = sample_preprocessed_data
    
    try:
        df = load_raw_data()
        result = compute_descriptors(df)
        
        # Verify that result contains original columns
        assert 'formula' in result.columns
        assert 'target_property' in result.columns
        
        # Verify that result contains new descriptor columns
        original_cols = set(df.columns)
        new_cols = [col for col in result.columns if col not in original_cols]
        assert len(new_cols) > 0, "No descriptor columns were created"
        
        # Verify L2-normalization: sum of squares of each row should be 1 (or close to it)
        descriptor_matrix = result[new_cols].values
        norms = np.linalg.norm(descriptor_matrix, axis=1)
        
        # Allow for small floating point errors
        assert np.allclose(norms, 1.0, atol=1e-5), "L2-normalization failed: norms are not 1.0"
        
    finally:
        # Restore original input path
        descriptors.INPUT_FILE = original_input

def test_compute_descriptors_missing_formula_column():
    """Test that compute_descriptors raises an error when formula column is missing."""
    df = pd.DataFrame({
        'some_column': [1, 2, 3],
        'target_property': [1.0, 2.0, 3.0]
    })
    
    with pytest.raises(ValueError, match="Input data must contain a 'formula' column"):
        compute_descriptors(df)

def test_save_descriptors(sample_preprocessed_data):
    """Test that save_descriptors correctly saves the dataframe to parquet."""
    import descriptors
    original_input = descriptors.INPUT_FILE
    original_output = descriptors.OUTPUT_FILE
    
    descriptors.INPUT_FILE = sample_preprocessed_data
    
    # Create a temporary output directory
    temp_dir = tempfile.mkdtemp()
    temp_output = Path(temp_dir) / "descriptors.parquet"
    descriptors.OUTPUT_FILE = temp_output
    
    try:
        df = load_raw_data()
        result = compute_descriptors(df)
        save_descriptors(result)
        
        # Verify that the output file exists
        assert temp_output.exists(), "Output file was not created"
        
        # Verify that the output file can be read
        loaded_df = pd.read_parquet(temp_output)
        assert len(loaded_df) == len(result), "Output dataframe has incorrect length"
        
    finally:
        # Restore original paths
        descriptors.INPUT_FILE = original_input
        descriptors.OUTPUT_FILE = original_output