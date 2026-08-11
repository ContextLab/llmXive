import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from requests.exceptions import RequestException
from data.ingestion import fetch_single_satellite, DataUnavailableError, PipelineError

@patch('data.ingestion.requests.Session')
def test_403_error_handling(mock_session):
    """Test that 403 Forbidden errors are caught and raise PipelineError."""
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.raise_for_status.side_effect = None
    mock_session.return_value.get.return_value = mock_response
    
    with pytest.raises(PipelineError) as exc_info:
        fetch_single_satellite("LAGEOS-1", "https://example.com/data.lrg")
    
    assert "Forbidden (403)" in str(exc_info.value)

@patch('data.ingestion.requests.Session')
def test_insufficient_data_warning(mock_session):
    """Test that datasets with <500 points raise DataUnavailableError."""
    # Create a mock response with a small DataFrame
    small_df = pd.DataFrame({'time': range(100), 'range': range(100)})
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = small_df.to_csv(index=False, sep=' ')
    mock_response.raise_for_status.return_value = None
    
    mock_session.return_value.get.return_value = mock_response
    
    with pytest.raises(DataUnavailableError) as exc_info:
        fetch_single_satellite("LAGEOS-1", "https://example.com/data.lrg")
    
    assert "Insufficient Data" in str(exc_info.value)
    assert "500" in str(exc_info.value)

@patch('data.ingestion.requests.Session')
def test_successful_fetch_with_sufficient_data(mock_session):
    """Test successful fetch when data >= 500 points."""
    large_df = pd.DataFrame({'time': range(600), 'range': range(600)})
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = large_df.to_csv(index=False, sep=' ')
    mock_response.raise_for_status.return_value = None
    
    mock_session.return_value.get.return_value = mock_response
    
    result = fetch_single_satellite("LAGEOS-1", "https://example.com/data.lrg")
    
    assert isinstance(result, pd.DataFrame)
    assert len(result) >= 500