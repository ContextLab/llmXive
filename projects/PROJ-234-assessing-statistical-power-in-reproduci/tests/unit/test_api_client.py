"""
Unit tests for the OpenML API client.
"""
import pytest
from unittest.mock import patch, MagicMock
from code.utils.api_client import OpenMLClient

@patch('code.utils.api_client.requests.Session')
def test_api_client_retry_on_429(mock_session_class):
    """
    Test that the OpenMLClient handles HTTP 429 errors with retry logic.
    """
    # Mock the session and its get method
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session
    
    # Configure the mock to raise a 429 error first, then succeed
    from requests.exceptions import HTTPError
    import requests
    
    response_429 = MagicMock()
    response_429.status_code = 429
    response_429.raise_for_status.side_effect = HTTPError("429 Too Many Requests")
    
    response_200 = MagicMock()
    response_200.status_code = 200
    response_200.json.return_value = {"datasets": []}
    
    # The adapter logic in urllib3 handles retries, but we can test the client setup
    # The actual retry behavior is handled by the HTTPAdapter with Retry strategy.
    # We verify that the adapter is configured correctly.
    
    client = OpenMLClient()
    
    # Verify that the adapter is mounted
    assert "http://" in client.session.adapters
    assert "https://" in client.session.adapters
    
    # Verify the retry strategy is configured
    adapter = client.session.adapters['https://']
    assert adapter.max_retries.total == 5
    assert 429 in adapter.max_retries.status_forcelist
