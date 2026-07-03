"""
Unit tests for the error handling infrastructure with exponential backoff.

These tests verify that:
1. Successful API calls return immediately without retries
2. Transient failures trigger exponential backoff retries
3. Non-retryable exceptions fail immediately
4. Rate limit errors are handled correctly
5. Maximum retry limits are enforced
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from code.infrastructure.error_handler import (
    exponential_backoff_retry,
    retry_with_backoff,
    APIRetryError,
    is_rate_limit_error,
    RateLimitAwareRetry
)


class TestExponentialBackoffRetry:
    """Tests for the exponential_backoff_retry decorator."""

    def test_successful_call_no_retries(self):
        """Test that successful calls return immediately without retries."""
        call_count = 0

        @exponential_backoff_retry(max_retries=3)
        def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_function()
        assert result == "success"
        assert call_count == 1

    def test_transient_failure_triggers_retries(self):
        """Test that transient failures trigger exponential backoff retries."""
        call_count = 0
        max_calls = 3

        @exponential_backoff_retry(
            max_retries=2,
            base_delay=0.01,  # Fast test
            jitter=False
        )
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < max_calls:
                raise ConnectionError("Transient network error")
            return "success"

        result = flaky_function()
        assert result == "success"
        assert call_count == max_calls

    def test_max_retries_exceeded_raises_error(self):
        """Test that exceeding max retries raises APIRetryError."""
        call_count = 0

        @exponential_backoff_retry(
            max_retries=2,
            base_delay=0.01,
            jitter=False
        )
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Persistent error")

        with pytest.raises(APIRetryError) as exc_info:
            always_fails()

        assert call_count == 3  # Initial + 2 retries
        assert exc_info.value.last_exception is not None
        assert isinstance(exc_info.value.last_exception, ConnectionError)

    def test_non_retryable_exception_fails_immediately(self):
        """Test that non-retryable exceptions fail without retries."""
        call_count = 0

        @exponential_backoff_retry(
            max_retries=3,
            base_delay=0.01,
            retryable_exceptions=(ConnectionError,)  # ValueError not included
        )
        def raises_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Non-retryable error")

        with pytest.raises(ValueError):
            raises_value_error()

        assert call_count == 1  # No retries

    def test_jitter_adds_randomness(self):
        """Test that jitter adds randomness to delays."""
        @exponential_backoff_retry(
            max_retries=1,
            base_delay=0.01,
            jitter=True
        )
        def flaky_with_jitter():
            raise ConnectionError("Error")

        # This test verifies the code runs without hanging
        # The actual jitter behavior is hard to test deterministically
        with pytest.raises(APIRetryError):
            flaky_with_jitter()


class TestRetryWithBackoff:
    """Tests for the retry_with_backoff function wrapper."""

    def test_function_wrapper_works(self):
        """Test that the function wrapper applies retry logic correctly."""
        call_count = 0

        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Error")
            return "success"

        wrapped_func = retry_with_backoff(
            flaky_func,
            max_retries=2,
            base_delay=0.01,
            jitter=False
        )

        result = wrapped_func()
        assert result == "success"
        assert call_count == 2


class TestIsRateLimitError:
    """Tests for rate limit error detection."""

    @pytest.mark.parametrize("message", [
        "429 Too Many Requests",
        "Rate limit exceeded",
        "Quota exceeded for API",
        "Too many requests, try again later",
        "Throttling: please wait",
    ])
    def test_rate_limit_messages_detected(self, message):
        """Test that various rate limit messages are detected."""
        assert is_rate_limit_error(Exception(message)) is True

    @pytest.mark.parametrize("message", [
        "Connection timeout",
        "Internal server error",
        "Not found",
        "Bad request",
    ])
    def test_non_rate_limit_messages(self, message):
        """Test that non-rate limit messages are not detected."""
        assert is_rate_limit_error(Exception(message)) is False


class TestRateLimitAwareRetry:
    """Tests for the RateLimitAwareRetry context manager."""

    def test_successful_execution(self):
        """Test successful execution without retries."""
        retry_manager = RateLimitAwareRetry(max_retries=3, base_delay=0.01)
        
        def success_func():
            return "success"

        result = retry_manager.execute(success_func)
        assert result == "success"

    def test_rate_limit_adjusts_delay(self):
        """Test that rate limit errors increase delay more aggressively."""
        call_count = 0
        
        def rate_limited_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("429 Too Many Requests")
            return "success"

        retry_manager = RateLimitAwareRetry(
            max_retries=2,
            base_delay=0.01,
            jitter=False
        )

        result = retry_manager.execute(rate_limited_func)
        assert result == "success"
        assert call_count == 2

    def test_max_retries_enforced(self):
        """Test that maximum retries are enforced."""
        def always_fails():
            raise Exception("429 Too Many Requests")

        retry_manager = RateLimitAwareRetry(max_retries=2, base_delay=0.01)

        with pytest.raises(APIRetryError):
            retry_manager.execute(always_fails)


class TestIntegration:
    """Integration tests for the error handling infrastructure."""

    def test_real_world_scenario(self):
        """Test a realistic API call scenario with mixed failures."""
        call_sequence = [
            ConnectionError("Network timeout"),
            ConnectionError("Network timeout"),
            Exception("429 Too Many Requests"),  # Rate limit
            "success"
        ]
        call_index = 0

        @exponential_backoff_retry(
            max_retries=5,
            base_delay=0.01,
            jitter=False
        )
        def api_call():
            nonlocal call_index
            if call_index < len(call_sequence) - 1:
                result = call_sequence[call_index]
                call_index += 1
                raise result
            return call_sequence[call_index]

        result = api_call()
        assert result == "success"
        assert call_index == len(call_sequence) - 1

    def test_custom_retryable_exceptions(self):
        """Test with custom retryable exception types."""
        class CustomAPIError(Exception):
            pass

        call_count = 0

        @exponential_backoff_retry(
            max_retries=2,
            base_delay=0.01,
            retryable_exceptions=(CustomAPIError,),
            jitter=False
        )
        def custom_error_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise CustomAPIError("Custom API error")
            return "success"

        result = custom_error_func()
        assert result == "success"
        assert call_count == 2
