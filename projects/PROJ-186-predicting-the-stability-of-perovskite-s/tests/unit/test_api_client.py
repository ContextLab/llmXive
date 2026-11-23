"""
tests/unit/test_api_client.py

Unit tests for the API client retry logic.
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.api_client import fetch_with_backoff, RateLimitedSession
from urllib3.exceptions import MaxRetryError

@patch('code.utils.api_client.requests.Session.get')
def test_retry_logic_triggers_on_429_error(mock_get):
    """
    Test that the retry logic is triggered when a 429 error is received.
    """
    # Setup mock to return 429 three times, then 200
    mock_response_429 = MagicMock()
    mock_response_429.status_code = 429
    mock_response_429.headers = {'Retry-After': '0'} # Ensure immediate retry capability in mock context if needed, though logic is in adapter

    mock_response_200 = MagicMock()
    mock_response_200.status_code = 200
    mock_response_200.text = "OK"

    # Sequence: 429, 429, 200
    mock_get.side_effect = [mock_response_429, mock_response_429, mock_response_200]

    # Call the function
    # Note: fetch_with_backoff uses a RateLimitedSession which has its own retry logic.
    # The mock replaces the .get method of the session instance used inside.
    response = fetch_with_backoff("https://example.com/api")

    # Check that get was called 3 times (2 retries + 1 success)
    # The adapter logic retries on status code 429.
    assert mock_get.call_count == 3
    assert response.status_code == 200

@patch('code.utils.api_client.requests.Session.get')
def test_retry_logic_raises_after_max_retries(mock_get):
    """Test that an exception is raised after max retries on 429."""
    mock_response_429 = MagicMock()
    mock_response_429.status_code = 429
    mock_response_429.headers = {'Retry-After': '0'}

    # Always return 429
    mock_get.return_value = mock_response_429

    # The Retry adapter in urllib3 raises MaxRetryError or RetryError if all retries fail.
    # We expect an exception to be raised.
    with pytest.raises((MaxRetryError, Exception)):
        fetch_with_backoff("https://example.com/api")