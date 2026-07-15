"""
Integration test for timeout/retry logic in the inference API client.

This test verifies that:
1. The API client respects the 120s timeout constraint.
2. The client implements exponential backoff retry logic on transient failures.
3. The client correctly propagates TimeoutError after max retries.

Dependencies:
- src.utils.timeout_utils (for timeout enforcement)
- src.execution.api_client (for the client implementation)
"""

import pytest
import time
import os
import sys
from unittest.mock import patch, MagicMock, PropertyMock
from requests.exceptions import RequestException, ConnectTimeout

# Add project root to path if running standalone
if "code" not in sys.path:
    code_root = os.path.join(os.path.dirname(__file__), "..", "..", "code")
    sys.path.insert(0, code_root)

from src.utils.timeout_utils import TimeoutError, run_with_api_timeout
from src.execution.api_client import call_inference_api

# Constants for test configuration
MAX_RETRIES = 3
INITIAL_BACKOFF = 0.1  # Short backoff for testing speed
TIMEOUT_SECONDS = 2    # Short timeout for testing speed

@pytest.fixture
def mock_response_success():
    """Mock a successful API response."""
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {
        "generated_text": "// Translated JavaScript code",
        "usage": {"prompt_tokens": 10, "completion_tokens": 20}
    }
    return mock

@pytest.fixture
def mock_response_timeout():
    """Mock a response that simulates a timeout/504 error."""
    mock = MagicMock()
    mock.status_code = 504
    mock.raise_for_status.side_effect = RequestException("Gateway Timeout")
    return mock

@pytest.fixture
def mock_response_connect_timeout():
    """Mock a connection timeout."""
    mock = MagicMock()
    mock.raise_for_status.side_effect = ConnectTimeout("Connection timed out")
    return mock

def test_inference_retry_on_transient_failure(mock_response_success, mock_response_timeout):
    """
    Test that the client retries on transient failures (504) and succeeds on the final attempt.
    """
    call_count = 0

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < MAX_RETRIES:
            return mock_response_timeout
        return mock_response_success

    with patch('src.execution.api_client.requests.post', side_effect=side_effect) as mock_post:
        # Run with a short timeout for the test
        result = call_inference_api(
            prompt="test prompt",
            model="test-model",
            max_retries=MAX_RETRIES,
            initial_backoff=INITIAL_BACKOFF,
            timeout=TIMEOUT_SECONDS
        )

        # Verify the request was made exactly MAX_RETRIES times
        assert mock_post.call_count == MAX_RETRIES
        # Verify the final result is the success response
        assert result is not None
        assert result.json()["generated_text"] == "// Translated JavaScript code"

def test_inference_timeout_propagation(mock_response_timeout):
    """
    Test that TimeoutError is raised after max retries are exhausted on transient failures.
    """
    call_count = 0

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return mock_response_timeout

    with patch('src.execution.api_client.requests.post', side_effect=side_effect):
        with pytest.raises(TimeoutError) as exc_info:
            call_inference_api(
                prompt="test prompt",
                model="test-model",
                max_retries=MAX_RETRIES,
                initial_backoff=INITIAL_BACKOFF,
                timeout=TIMEOUT_SECONDS
            )

        # Verify the error message indicates retries were exhausted
        assert "Max retries exceeded" in str(exc_info.value)
        assert "Timeout" in str(exc_info.value)

def test_inference_connection_timeout_handling(mock_response_connect_timeout):
    """
    Test that connection timeouts are handled as transient failures and trigger retries.
    """
    call_count = 0

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < MAX_RETRIES:
            return mock_response_connect_timeout
        # Simulate success on last try
        mock_success = MagicMock()
        mock_success.status_code = 200
        mock_success.json.return_value = {"generated_text": "success"}
        return mock_success

    with patch('src.execution.api_client.requests.post', side_effect=side_effect) as mock_post:
        result = call_inference_api(
            prompt="test prompt",
            model="test-model",
            max_retries=MAX_RETRIES,
            initial_backoff=INITIAL_BACKOFF,
            timeout=TIMEOUT_SECONDS
        )

        assert mock_post.call_count == MAX_RETRIES
        assert result is not None

def test_inference_enforces_timeout_decorator(mock_response_success):
    """
    Test that the run_with_api_timeout decorator correctly enforces the timeout.
    """
    def slow_function():
        time.sleep(TIMEOUT_SECONDS + 1)
        return "result"

    with pytest.raises(TimeoutError):
        run_with_api_timeout(timeout=TIMEOUT_SECONDS)(slow_function)()

    # Verify a fast function passes through
    def fast_function():
        return "fast"

    result = run_with_api_timeout(timeout=TIMEOUT_SECONDS)(fast_function)()
    assert result == "fast"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])