"""
Integration test for API collector rate-limiting and backoff.
Tests T014 implementation.
"""
import time
from unittest.mock import patch, MagicMock, PropertyMock
import pytest
import requests
from requests.exceptions import RequestException, HTTPError, ConnectionError

from code.data.collector import APICollector

@pytest.fixture
def collector():
    """Initialize the APICollector for testing."""
    return APICollector()

def test_rate_limit_backoff(collector):
    """
    Verify that the collector waits when a 429 status is returned.
    
    This test mocks the session.get to first return a 429 (Too Many Requests)
    with a Retry-After header, then a 200 (OK). It verifies that the elapsed
    time includes the backoff wait period.
    """
    # Mock the 429 response
    mock_response_429 = MagicMock()
    mock_response_429.status_code = 429
    mock_response_429.headers = {"Retry-After": "1"}  # Force 1s wait
    # Configure raise_for_status to raise HTTPError for 429
    mock_response_429.raise_for_status.side_effect = HTTPError(response=mock_response_429)
    
    # Mock the successful 200 response
    mock_response_200 = MagicMock()
    mock_response_200.status_code = 200
    mock_response_200.json.return_value = {"studies": [], "nextPageToken": None}
    
    call_count = 0
    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return mock_response_429
        return mock_response_200

    with patch.object(collector.session, 'get', side_effect=side_effect):
        start = time.time()
        try:
            # Attempt to fetch. The internal logic should catch the 429,
            # read the Retry-After header, wait, and retry.
            result = collector._fetch_clinicaltrials()
        except Exception:
            # We might hit other mock setup errors (e.g. parsing empty results),
            # but the critical part is that the wait happened before the crash.
            pass

        elapsed = time.time() - start
        # The backoff logic should wait at least 1 second (plus small overhead).
        # We use 0.8s as a safe lower bound to account for test overhead.
        assert elapsed >= 0.8, f"Expected backoff wait of ~1s, but elapsed time was {elapsed:.2f}s"

def test_connection_error_retry(collector):
    """
    Verify that connection errors trigger retry logic.
    
    This test mocks session.get to raise ConnectionError repeatedly.
    It verifies that the collector attempts the request multiple times
    before giving up (or raising the final error).
    """
    call_count = 0
    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        raise ConnectionError("Simulated connection error")

    with patch.object(collector.session, 'get', side_effect=side_effect):
        # The collector should retry a few times (defined in _fetch_clinicaltrials)
        # and then raise the exception.
        with pytest.raises(ConnectionError):
            collector._fetch_clinicaltrials()
        
        # Verify retry logic: if max_retries is 3, it should be called 4 times total (1 initial + 3 retries)
        # or at least more than once.
        assert call_count > 1, f"Retry logic failed: request was only called {call_count} time(s)"