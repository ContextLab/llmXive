"""
Tests for the ingestion module.

Specifically tests the "fail loudly" behavior when data fetch fails.
"""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from datasets.exceptions import DatasetNotFoundError

# Add parent directory to path to import code modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'code')))

from ingestion import load_glass_data

def test_load_glass_data_fails_loudly():
    """
    Test that load_glass_data raises ValueError if the dataset fetch fails.
    This verifies the 'fail loudly' requirement of T008.
    """
    # Mock the load_dataset function to simulate a failure
    with patch('ingestion.load_dataset') as mock_load:
        # Simulate the specific error raised by the datasets library
        mock_load.side_effect = DatasetNotFoundError("Dataset 'matsci/glass-forming-ability' doesn't exist")
        
        # Assert that ValueError is raised
        with pytest.raises(ValueError) as exc_info:
            load_glass_data()
        
        # Verify the error message contains the expected text
        assert "Data fetch failed" in str(exc_info.value)
        assert "matsci/glass-forming-ability" in str(exc_info.value)
        assert "unavailable" in str(exc_info.value)

def test_load_glass_data_success():
    """
    Test that load_glass_data returns a DataFrame on success.
    """
    # Mock the load_dataset function to return a mock dataset
    mock_dataset = {
        'train': [
            {'composition': 'Fe_Cr_Ni', 'critical_cooling_rate': 100.0},
            {'composition': 'Cu_Zr_Al', 'critical_cooling_rate': 50.0}
        ]
    }
    
    with patch('ingestion.load_dataset') as mock_load:
        mock_load.return_value = mock_dataset
        
        df = load_glass_data()
        
        # Basic check that we got data back
        assert df is not None
        assert len(df) == 2
        assert 'composition' in df.columns
        assert 'critical_cooling_rate' in df.columns
