import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import the function to test
from code.src.data_loader import generate_injection_ground_truth, load_slfc_dataset
from code.src.utils import angular_distance

@pytest.fixture
def mock_slfc_dataset():
    """Create a small mock SLFC dataset for testing."""
    np.random.seed(123)
    n = 100
    data = {
        'ra': np.random.uniform(0, 10, n),
        'dec': np.random.uniform(0, 10, n),
        'is_lens': np.random.choice([0, 1], n),
        'snr': np.random.uniform(5, 20, n),
        'morphology': np.random.uniform(0.3, 0.9, n)
    }
    return pd.DataFrame(data)

def test_generate_injection_ground_truth(mock_slfc_dataset):
    """Test that injection ground truth is generated correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "injection_ground_truth.csv"
        
        # Run the function
        generate_injection_ground_truth(mock_slfc_dataset, str(output_path))
        
        # Verify file exists
        assert output_path.exists(), "Output file was not created."
        
        # Verify contents
        df = pd.read_csv(output_path)
        
        # Check columns
        assert list(df.columns) == ['RA', 'Dec', 'injected_id'], "Incorrect columns."
        
        # Check count (should be close to 500, but might be less if bounds are tight)
        # With a 10x10 box and 2 arcsec min distance, we can fit many.
        # We expect a significant number.
        assert len(df) > 0, "No injections were generated."
        
        # Check uniqueness of IDs
        assert len(df['injected_id'].unique()) == len(df), "Injected IDs are not unique."
        
        # Check coordinate ranges
        assert df['RA'].min() >= mock_slfc_dataset['ra'].min()
        assert df['RA'].max() <= mock_slfc_dataset['ra'].max()
        assert df['Dec'].min() >= mock_slfc_dataset['dec'].min()
        assert df['Dec'].max() <= mock_slfc_dataset['dec'].max()
        
        # Check separation
        for i in range(len(df)):
            for j in range(i + 1, len(df)):
                dist = angular_distance(df.iloc[i]['RA'], df.iloc[i]['Dec'], 
                                      df.iloc[j]['RA'], df.iloc[j]['Dec'])
                assert dist >= 2.0 - 1e-6, f"Injections {i} and {j} are too close: {dist}"

def test_generate_injection_ground_truth_empty_input():
    """Test that an empty DataFrame raises an error."""
    empty_df = pd.DataFrame(columns=['ra', 'dec', 'is_lens'])
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "injection_ground_truth.csv"
        with pytest.raises(Exception): # DataIngestionError
            generate_injection_ground_truth(empty_df, str(output_path))

def test_injection_id_format():
    """Test that injected IDs follow the expected format."""
    mock_df = pd.DataFrame({
        'ra': [0.0], 'dec': [0.0], 'is_lens': [0], 'snr': [10], 'morphology': [0.5]
    })
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "injection_ground_truth.csv"
        generate_injection_ground_truth(mock_df, str(output_path))
        df = pd.read_csv(output_path)
        for id_str in df['injected_id']:
            assert id_str.startswith("inject_"), f"ID {id_str} does not start with 'inject_'"
            # Check it has 5 digits
            suffix = id_str.split("_")[1]
            assert len(suffix) == 5, f"ID suffix {suffix} is not 5 digits"
