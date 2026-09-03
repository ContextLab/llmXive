"""
Tests for T018: Error handling for 403 errors and "Insufficient Data" warnings.
"""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import requests
from io import StringIO
from data.ingestion import (
    fetch_single_satellite, 
    fetch_all_satellites, 
    verify_data_availability,
    DataIngestionError,
    get_satellite_urls
)
from utils.logging import get_logger

logger = get_logger(__name__)

@pytest.fixture
def mock_config_urls():
    """Mock configuration with satellite URLs."""
    return {
        "LAGEOS-1": "https://example.com/lageos1.csv",
        "LAGEOS-2": "https://example.com/lageos2.csv",
        "ETALON-1": "https://example.com/etalon1.csv"
    }

@patch('data.ingestion.get_config')
def test_403_error_handling(mock_get_config, mock_config_urls):
    """Test that 403 Forbidden errors are caught and handled properly."""
    # Setup mock config
    mock_config = MagicMock()
    mock_config.verified_dataset_urls = mock_config_urls
    mock_get_config.return_value = mock_config

    # Mock requests.get to return 403
    with patch('data.ingestion.requests.Session') as mock_session_class:
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        # Configure the mock to return 403
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("403 Client Error")
        mock_session.get.return_value = mock_response

        # Verify that verify_data_availability catches the 403
        is_available, message = verify_data_availability("https://example.com/test.csv")
        
        assert is_available == False
        assert "403" in message
        assert "Forbidden" in message

@patch('data.ingestion.get_config')
def test_insufficient_data_warning(mock_get_config, mock_config_urls):
    """Test that datasets with <500 points trigger an Insufficient Data warning."""
    # Setup mock config
    mock_config = MagicMock()
    mock_config.verified_dataset_urls = mock_config_urls
    mock_get_config.return_value = mock_config

    # Create a small CSV with only 100 points
    small_csv_data = "time,residual\n" + "\n".join([f"{i},{i*0.1}" for i in range(100)])
    
    with patch('data.ingestion.requests.Session') as mock_session_class:
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = small_csv_data
        mock_session.get.return_value = mock_response

        # Verify that verify_data_availability catches insufficient data
        is_available, message = verify_data_availability("https://example.com/small.csv", min_points=500)
        
        assert is_available == False
        assert "Insufficient Data" in message
        assert "100" in message
        assert "500" in message

@patch('data.ingestion.get_config')
def test_fetch_single_satellite_403(mock_get_config, mock_config_urls):
    """Test that fetch_single_satellite raises DataIngestionError on 403."""
    mock_config = MagicMock()
    mock_config.verified_dataset_urls = mock_config_urls
    mock_get_config.return_value = mock_config

    with patch('data.ingestion.requests.Session') as mock_session_class:
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        # Mock 403 in verify step
        mock_response_head = MagicMock()
        mock_response_head.status_code = 403
        mock_session.head.return_value = mock_response_head

        with pytest.raises(DataIngestionError) as exc_info:
            fetch_single_satellite("LAGEOS-1", "https://example.com/lageos1.csv")
        
        assert "403" in str(exc_info.value)
        assert "Forbidden" in str(exc_info.value)

@patch('data.ingestion.get_config')
def test_fetch_single_satellite_insufficient_data(mock_get_config, mock_config_urls):
    """Test that fetch_single_satellite raises DataIngestionError on insufficient data."""
    mock_config = MagicMock()
    mock_config.verified_dataset_urls = mock_config_urls
    mock_get_config.return_value = mock_config

    small_csv_data = "time,residual\n" + "\n".join([f"{i},{i*0.1}" for i in range(100)])
    
    with patch('data.ingestion.requests.Session') as mock_session_class:
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        # Mock successful HEAD but insufficient data in GET
        mock_response_head = MagicMock()
        mock_response_head.status_code = 200
        mock_session.head.return_value = mock_response_head
        
        mock_response_get = MagicMock()
        mock_response_get.status_code = 200
        mock_response_get.text = small_csv_data
        mock_session.get.return_value = mock_response_get

        with pytest.raises(DataIngestionError) as exc_info:
            fetch_single_satellite("LAGEOS-1", "https://example.com/lageos1.csv")
        
        assert "Insufficient Data" in str(exc_info.value)

@patch('data.ingestion.get_config')
def test_fetch_all_satellites_partial_failure(mock_get_config, mock_config_urls):
    """Test that fetch_all_satellites handles partial failures gracefully."""
    mock_config = MagicMock()
    mock_config.verified_dataset_urls = mock_config_urls
    mock_get_config.return_value = mock_config

    # Mock data for successful satellites
    good_csv = "time,residual\n" + "\n".join([f"{i},{i*0.1}" for i in range(600)])
    small_csv = "time,residual\n" + "\n".join([f"{i},{i*0.1}" for i in range(100)])

    call_count = [0]
    
    def mock_get_side_effect(url, **kwargs):
        call_count[0] += 1
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        if "lageos1" in url.lower():
            mock_resp.text = good_csv
        elif "lageos2" in url.lower():
            mock_resp.text = small_csv  # Will fail verification
        else:
            mock_resp.text = good_csv
        return mock_resp

    with patch('data.ingestion.requests.Session') as mock_session_class:
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.get.side_effect = mock_get_side_effect
        mock_session.head.return_value = MagicMock(status_code=200)

        # Should succeed with partial data but warn about failures
        df = fetch_all_satellites(["LAGEOS-1", "LAGEOS-2", "ETALON-1"])
        
        # Should have data from LAGEOS-1 and ETALON-1 (600 + 600 = 1200)
        # LAGEOS-2 should be skipped due to insufficient data
        assert len(df) == 1200
        assert "LAGEOS-2" not in df['satellite_id'].values

@patch('data.ingestion.get_config')
def test_verify_data_availability_success(mock_get_config, mock_config_urls):
    """Test successful verification of sufficient data."""
    mock_config = MagicMock()
    mock_config.verified_dataset_urls = mock_config_urls
    mock_get_config.return_value = mock_config

    good_csv = "time,residual\n" + "\n".join([f"{i},{i*0.1}" for i in range(1000)])
    
    with patch('data.ingestion.requests.Session') as mock_session_class:
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response_head = MagicMock(status_code=200)
        mock_session.head.return_value = mock_response_head
        
        mock_response_get = MagicMock()
        mock_response_get.status_code = 200
        mock_response_get.text = good_csv
        mock_session.get.return_value = mock_response_get

        is_available, message = verify_data_availability("https://example.com/good.csv", min_points=500)
        
        assert is_available == True
        assert "Insufficient Data" not in message
        assert "1000" in message