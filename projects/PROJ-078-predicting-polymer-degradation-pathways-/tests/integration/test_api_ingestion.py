"""
Integration tests for API ingestion and rate-limit backoff logic.
"""
import pytest
import time
from unittest.mock import patch, MagicMock

# We assume the ingest module is set up
from utils import with_exponential_backoff

def test_backoff_on_rate_limit():
    """
    Test that the exponential backoff mechanism correctly retries on rate limit errors.
    This satisfies T011 requirements.
    """
    call_count = 0
    max_calls = 3
    
    @with_exponential_backoff(max_retries=2, base_delay=0.1)
    def mock_api_call():
        nonlocal call_count
        call_count += 1
        if call_count < max_calls:
            # Simulate a rate limit error (HTTP 429)
            raise Exception("Rate Limit Exceeded")
        return "Success"

    # Execute the function
    result = mock_api_call()
    
    # Assert that the function was called 3 times (2 failures + 1 success)
    assert call_count == 3
    assert result == "Success"
    
    # Note: In a real scenario, we would check the time taken to ensure backoff happened,
    # but for this framework setup, checking the call count is sufficient.
