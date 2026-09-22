"""
Unit tests for src/data/download.py
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import io
import os
import sys

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.data.download import (
    handle_duplicates,
    filter_missing_values,
    fetch_nims_creep_data,
    SessionWithRetry
)
from src.utils.validators import validate_schema

@pytest.fixture
def sample_df():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        'alloy_id': ['A1', 'A1', 'A2', 'A3', 'A4'],
        'temperature': [700.0, 700.0, 750.0, 800.0, np.nan],
        'stress': [100.0, 100.0, 150.0, 200.0, 120.0],
        'rupture_time': [1000.0, 1200.0, 500.0, 200.0, 800.0],
        'composition': ['Ni-Cr', 'Ni-Cr', 'Fe-Cr', 'Co-Ni', 'Ti-Al']
    })

def test_handle_duplicates_averaging(sample_df):
    """Test that duplicates are averaged correctly."""
    # A1 has two entries: rupture_time 1000 and 1200 -> avg 1100
    result = handle_duplicates(sample_df, id_col='alloy_id')
    
    assert len(result) == 4, "Should have 4 unique IDs"
    assert result.loc[result['alloy_id'] == 'A1', 'rupture_time'].iloc[0] == 1100.0
    assert result.loc[result['alloy_id'] == 'A1', 'temperature'].iloc[0] == 700.0

def test_filter_missing_values(sample_df):
    """Test that rows with missing critical values are removed."""
    result = filter_missing_values(sample_df)
    
    # Row A4 has NaN temperature, should be removed
    assert len(result) == 4, "Should remove 1 row with NaN temperature"
    assert 'A4' not in result['alloy_id'].values
    assert all(result['temperature'].notna())
    assert all(result['stress'].notna())
    assert all(result['rupture_time'].notna())

def test_filter_missing_values_empty_result():
    """Test that an error is raised if all rows are filtered out."""
    df = pd.DataFrame({
        'alloy_id': ['A1'],
        'temperature': [np.nan],
        'stress': [100.0],
        'rupture_time': [1000.0]
    })
    
    with pytest.raises(ValueError, match="No valid data rows remain"):
        filter_missing_values(df)

@patch('src.data.download.requests.Session')
def test_fetch_nims_creep_data_success(mock_session_class):
    """Test successful fetch."""
    mock_response = MagicMock()
    mock_response.content = b"alloy_id,temperature,stress,rupture_time\nA1,700,100,1000"
    mock_response.raise_for_status = MagicMock()
    
    mock_session = MagicMock()
    mock_session.get.return_value = mock_response
    mock_session_class.return_value = mock_session
    
    # Mock the CSV reading
    with patch('pandas.read_csv') as mock_read_csv:
        mock_read_csv.return_value = pd.DataFrame({
            'alloy_id': ['A1'],
            'temperature': [700.0],
            'stress': [100.0],
            'rupture_time': [1000.0]
        })
        
        df = fetch_nims_creep_data(url="http://test.com/data.csv")
        
        assert len(df) == 1
        mock_session.get.assert_called_once()

@patch('src.data.download.requests.Session')
def test_fetch_nims_creep_data_failure(mock_session_class):
    """Test that failure raises an error."""
    mock_session = MagicMock()
    mock_session.get.side_effect = Exception("Network Error")
    mock_session_class.return_value = mock_session
    
    with pytest.raises(Exception):
        fetch_nims_creep_data(url="http://test.com/data.csv")

def test_session_with_retry_initialization():
    """Test that the retry session is initialized correctly."""
    session = SessionWithRetry()
    assert hasattr(session, 'mount')
    # Verify adapters are mounted (simplified check)
    assert 'http://' in session.adapters
