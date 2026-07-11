"""
Unit tests for the data ingestion module.
"""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import os
import sys

# Add project root to path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.src.data.ingest import (
    fetch_data_from_url,
    clean_data,
    validate_schema,
    run_ingestion
)

def test_clean_data_removes_missing_yield_strength():
    """Test that rows with missing yield strength are removed (FR-001)."""
    data = {
        'Yield_Strength': [250.0, 300.0, None, 400.0, None],
        'Carbon': [0.2, 0.3, 0.25, 0.35, 0.4]
    }
    df = pd.DataFrame(data)
    
    cleaned_df = clean_data(df)
    
    assert len(cleaned_df) == 2
    assert cleaned_df['Yield_Strength'].isna().sum() == 0
    assert list(cleaned_df['Carbon']) == [0.2, 0.3]

def test_validate_schema_returns_true():
    """Test schema validation with valid columns."""
    data = {
        'Yield_Strength': [250.0],
        'Carbon': [0.2]
    }
    df = pd.DataFrame(data)
    assert validate_schema(df) is True

def test_validate_schema_returns_false():
    """Test schema validation with missing target column."""
    data = {
        'Tensile_Strength': [500.0],
        'Carbon': [0.2]
    }
    df = pd.DataFrame(data)
    assert validate_schema(df) is False

@patch('code.src.data.ingest.requests.get')
def test_fetch_data_from_url_success(mock_get):
    """Test successful data fetching."""
    mock_response = MagicMock()
    mock_response.text = "Yield_Strength,Carbon\n250.0,0.2\n300.0,0.3"
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response
    
    df = fetch_data_from_url("http://example.com/data.csv")
    
    assert df is not None
    assert len(df) == 2
    assert 'Yield_Strength' in df.columns

@patch('code.src.data.ingest.requests.get')
def test_fetch_data_from_url_failure(mock_get):
    """Test data fetching failure."""
    mock_get.side_effect = Exception("Network error")
    
    df = fetch_data_from_url("http://example.com/data.csv")
    
    assert df is None