import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import requests
from io import StringIO

from code.data.ingestion import fetch_single_satellite, DataUnavailableError, verify_data_availability, get_satellite_urls

@pytest.fixture
def mock_config():
    """Mock configuration with verified URLs."""
    return {
        'verified_dataset_urls': {
            'LAGEOS-1': 'https://example.com/lageos1.csv',
            'LAGEOS-2': 'https://example.com/lageos2.csv',
            'Etalon-1': 'https://example.com/etalon1.csv'
        }
    }

@patch('code.data.ingestion.get_config')
def test_verify_data_availability(mock_get_config, mock_config):
    mock_get_config.return_value = type('Config', (), mock_config)()
    assert verify_data_availability() is True

@patch('code.data.ingestion.get_config')
def test_verify_data_availability_empty(mock_get_config):
    mock_get_config.return_value = type('Config', (), {'verified_dataset_urls': {}})()
    assert verify_data_availability() is False

@patch('code.data.ingestion.get_config')
def test_get_satellite_urls(mock_get_config, mock_config):
    mock_get_config.return_value = type('Config', (), mock_config)()
    urls = get_satellite_urls()
    assert 'LAGEOS-1' in urls
    assert urls['LAGEOS-1'] == 'https://example.com/lageos1.csv'

@patch('code.data.ingestion.requests.Session')
def test_fetch_single_satellite_success(mock_session_class):
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session
    
    # Mock response
    mock_response = MagicMock()
    mock_response.text = "time,range,residual\n1.0,1000.0,0.5\n2.0,1000.1,0.6\n"
    mock_response.headers = {'Content-Type': 'text/csv'}
    mock_response.raise_for_status = MagicMock()
    mock_session.get.return_value = mock_response

    df = fetch_single_satellite('LAGEOS-1', 'https://example.com/data.csv')
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert 'time' in df.columns
    assert df['satellite_id'].empty  # This function doesn't add satellite_id

@patch('code.data.ingestion.requests.Session')
def test_fetch_single_satellite_empty_content(mock_session_class):
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session
    
    mock_response = MagicMock()
    mock_response.text = ""
    mock_response.headers = {}
    mock_response.raise_for_status = MagicMock()
    mock_session.get.return_value = mock_response

    with pytest.raises(DataUnavailableError, match="No data content received"):
        fetch_single_satellite('LAGEOS-1', 'https://example.com/data.csv')

@patch('code.data.ingestion.requests.Session')
def test_fetch_single_satellite_retry_logic(mock_session_class):
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session
    
    # Simulate a transient error followed by success
    error_response = MagicMock()
    error_response.status_code = 503
    error_response.raise_for_status.side_effect = requests.exceptions.HTTPError("503 Service Unavailable")
    
    success_response = MagicMock()
    success_response.text = "time,range\n1.0,1000.0\n"
    success_response.headers = {'Content-Type': 'text/csv'}
    success_response.raise_for_status = MagicMock()
    
    mock_session.get.side_effect = [
        requests.exceptions.HTTPError("503"), # First call fails
        requests.exceptions.HTTPError("503"), # Second call fails
        success_response # Third call succeeds
    ]

    df = fetch_single_satellite('LAGEOS-1', 'https://example.com/data.csv')
    assert len(df) == 1
    assert mock_session.get.call_count == 3

@patch('code.data.ingestion.requests.Session')
def test_fetch_single_satellite_max_retries_exceeded(mock_session_class):
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session
    
    error_response = MagicMock()
    error_response.status_code = 503
    error_response.raise_for_status.side_effect = requests.exceptions.HTTPError("503 Service Unavailable")
    mock_session.get.return_value = error_response
    mock_session.get.side_effect = [error_response] * 6 # Force failure after retries

    with pytest.raises(DataUnavailableError):
        fetch_single_satellite('LAGEOS-1', 'https://example.com/data.csv')

@patch('code.data.ingestion.requests.Session')
def test_fetch_single_satellite_invalid_format(mock_session_class):
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session
    
    mock_response = MagicMock()
    mock_response.text = "This is not a valid CSV or table"
    mock_response.headers = {'Content-Type': 'text/plain'}
    mock_response.raise_for_status = MagicMock()
    mock_session.get.return_value = mock_response

    with pytest.raises(ValueError, match="Could not parse data"):
        fetch_single_satellite('LAGEOS-1', 'https://example.com/data.csv')