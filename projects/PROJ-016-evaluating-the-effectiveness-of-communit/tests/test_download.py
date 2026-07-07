"""
Unit tests for data download logic, specifically retry mechanisms.
"""
import pytest
import time
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.download import fetch_fao_fra_data

@patch('data.download.requests.get')
def test_503_retry_logic(mock_get):
    """
    Test that the function retries on 503 errors with exponential backoff.
    """
    # Setup mock to return 503 twice, then 200
    mock_response_fail = MagicMock()
    mock_response_fail.status_code = 503
    mock_response_fail.text = "Service Unavailable"

    mock_response_success = MagicMock()
    mock_response_success.status_code = 200
    mock_response_success.json.return_value = {
        "data": [
            {"country": "USA", "year": 2000, "value": 100}
        ]
    }

    # Sequence: Fail, Fail, Success
    mock_get.side_effect = [
        mock_response_fail,
        mock_response_fail,
        mock_response_success
    ]

    # Call function with max_retries=3, backoff_factor=0.1 (for speed in test)
    result = fetch_fao_fra_data(years=[2000], max_retries=3, backoff_factor=0.1)

    # Assertions
    assert mock_get.call_count == 3
    assert result is not None
    assert len(result) == 1
    assert result[0]["country"] == "USA"

@patch('data.download.requests.get')
def test_non_503_error_no_retry(mock_get):
    """
    Test that non-503 errors (e.g., 404) do not trigger retries.
    """
    mock_response_404 = MagicMock()
    mock_response_404.status_code = 404
    mock_response_404.text = "Not Found"
    mock_get.return_value = mock_response_404

    result = fetch_fao_fra_data(years=[2000], max_retries=3, backoff_factor=0.1)

    # Should only be called once because 404 is not retried
    assert mock_get.call_count == 1
    assert result is None

@patch('data.download.requests.get')
def test_request_exception_retry(mock_get):
    """
    Test that network exceptions trigger retries.
    """
    import requests
    
    # First two calls raise exception, third succeeds
    mock_response_success = MagicMock()
    mock_response_success.status_code = 200
    mock_response_success.json.return_value = {"data": []}

    mock_get.side_effect = [
        requests.exceptions.ConnectionError("Network error"),
        requests.exceptions.ConnectionError("Network error"),
        mock_response_success
    ]

    result = fetch_fao_fra_data(years=[2000], max_retries=3, backoff_factor=0.1)

    assert mock_get.call_count == 3
    # Result might be empty list but function should not crash
    assert result is not None