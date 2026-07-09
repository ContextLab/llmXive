"""
Integration test for API collector rate-limiting and backoff.
Tests T014 implementation.
"""
import time
from unittest.mock import patch, MagicMock
import pytest
import requests
from requests.exceptions import RequestException

from code.data.collector import APICollector

@pytest.fixture
def collector():
    return APICollector()

def test_rate_limit_backoff(collector):
    """
    Verify that the collector waits when a 429 status is returned.
    """
    # Mock the session.get to return 429 then 200
    mock_response_429 = MagicMock()
    mock_response_429.status_code = 429
    mock_response_429.headers = {"Retry-After": "1"} # Force 1s wait
    mock_response_429.raise_for_status.side_effect = requests.HTTPError(response=mock_response_429)

    mock_response_200 = MagicMock()
    mock_response_200.status_code = 200
    mock_response_200.json.return_value = {"studies": [], "nextPageToken": None}
    
    # Sequence: 429, then 200
    call_count = 0
    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return mock_response_429
        return mock_response_200

    with patch.object(collector.session, 'get', side_effect=side_effect):
        start = time.time()
        # We expect it to hit 429, wait 1s, then succeed
        try:
            # Note: The actual fetch method has internal loops. 
            # We are testing the _rate_limit_wait behavior indirectly via the flow.
            # For a strict unit test of the wait, we could test _rate_limit_wait directly,
            # but this tests the integration of the session and the wait logic.
            result = collector._fetch_clinicaltrials()
        except Exception:
            pass # We might hit other errors in the mock setup, but the wait should have happened

        elapsed = time.time() - start
        # If backoff worked, we should have waited at least 1 second
        # Allow small tolerance for test overhead
        assert elapsed >= 0.8, f"Expected backoff wait, but elapsed time was {elapsed:.2f}s"

def test_connection_error_retry(collector):
    """
    Verify that connection errors trigger retry logic.
    """
    call_count = 0
    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        raise requests.ConnectionError("Simulated connection error")

    with patch.object(collector.session, 'get', side_effect=side_effect):
        # This should trigger retries and eventually raise
        with pytest.raises(requests.ConnectionError):
            collector._fetch_clinicaltrials()
        
        # Verify it was called more than once (retry logic)
        assert call_count > 1, "Retry logic should have retried the request"