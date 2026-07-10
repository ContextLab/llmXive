"""
Unit tests for the data_loader module.
"""
import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from unittest.mock import patch, MagicMock
import sys
import importlib

# Add the code/src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code', 'src'))

@pytest.fixture
def mock_slfc_dataframe():
    """Create a mock SLFC DataFrame for testing."""
    data = {
        'ra_deg': np.random.uniform(0, 360, 100),
        'dec_deg': np.random.uniform(-90, 90, 100),
        'is_lens': np.random.choice([0, 1], 100)
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_generate_injection_ground_truth(mock_slfc_dataframe, temp_output_dir):
    """Test that generate_injection_ground_truth creates a valid CSV file."""
    # Import the function after setting up the path
    from data_loader import generate_injection_ground_truth
    
    output_path = os.path.join(temp_output_dir, "test_injection.csv")
    num_injections = 50
    
    # Run the function
    result_df = generate_injection_ground_truth(
        mock_slfc_dataframe, 
        output_path, 
        num_injections=num_injections,
        seed=42
    )
    
    # Verify the output file exists
    assert os.path.exists(output_path), "Output file was not created"
    
    # Verify the DataFrame structure
    assert 'RA' in result_df.columns, "RA column missing"
    assert 'Dec' in result_df.columns, "Dec column missing"
    assert 'injected_id' in result_df.columns, "injected_id column missing"
    
    # Verify the number of injections
    assert len(result_df) == num_injections, f"Expected {num_injections} rows, got {len(result_df)}"
    
    # Verify RA and Dec are within bounds
    assert result_df['RA'].min() >= mock_slfc_dataframe['ra_deg'].min()
    assert result_df['RA'].max() <= mock_slfc_dataframe['ra_deg'].max()
    assert result_df['Dec'].min() >= mock_slfc_dataframe['dec_deg'].min()
    assert result_df['Dec'].max() <= mock_slfc_dataframe['dec_deg'].max()
    
    # Verify injected_id format
    assert result_df['injected_id'].iloc[0].startswith("inject_"), "Injected ID format incorrect"
    
    # Verify reproducibility with seed
    result_df_2 = generate_injection_ground_truth(
        mock_slfc_dataframe, 
        output_path, 
        num_injections=num_injections,
        seed=42
    )
    assert result_df.equals(result_df_2), "Results not reproducible with same seed"

def test_generate_injection_ground_truth_missing_columns(mock_slfc_dataframe, temp_output_dir):
    """Test that generate_injection_ground_truth raises error when RA/Dec missing."""
    from data_loader import generate_injection_ground_truth
    
    # Remove RA and Dec columns
    df_no_coords = mock_slfc_dataframe.drop(columns=['ra_deg', 'dec_deg'])
    output_path = os.path.join(temp_output_dir, "test_injection.csv")
    
    with pytest.raises(FileNotFoundError, match="Could not find RA and Dec columns"):
        generate_injection_ground_truth(df_no_coords, output_path)

def test_generate_injection_ground_truth_different_seed(mock_slfc_dataframe, temp_output_dir):
    """Test that different seeds produce different results."""
    from data_loader import generate_injection_ground_truth
    
    output_path = os.path.join(temp_output_dir, "test_injection.csv")
    num_injections = 50
    
    result_df_1 = generate_injection_ground_truth(
        mock_slfc_dataframe, 
        output_path, 
        num_injections=num_injections,
        seed=42
    )
    
    result_df_2 = generate_injection_ground_truth(
        mock_slfc_dataframe, 
        output_path, 
        num_injections=num_injections,
        seed=123
    )
    
    # They should be different (with very high probability)
    assert not result_df_1.equals(result_df_2), "Different seeds should produce different results"