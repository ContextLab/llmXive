"""
Unit tests for the retry logic with exponential backoff.
"""

import pytest
import time
from unittest.mock import patch, MagicMock
from requests.exceptions import RequestException, Timeout

from utils.retry import (
    retry_with_backoff,
    retry_call,
    calculate_backoff,
    DEFAULT_MAX_RETRIES,
    DEFAULT_BASE_DELAY,
    RETRYABLE_EXCEPTIONS,
)


class TestCalculateBackoff:
    def test_exponential_growth(self):
        """Verify that delay grows exponentially with attempt number."""
        base = 1.0
        # Attempt 0: 1 * 2^0 = 1
        assert calculate_backoff(0, base_delay=base, jitter_factor=0) == base
        # Attempt 1: 1 * 2^1 = 2
        assert calculate_backoff(1, base_delay=base, jitter_factor=0) == base * 2
        # Attempt 2: 1 * 2^2 = 4
        assert calculate_backoff(2, base_delay=base, jitter_factor=0) == base * 4

    def test_max_delay_cap(self):
        """Verify that delay does not exceed max_delay."""
        max_d = 10.0
        # Large attempt number would normally be huge, but should be capped
        delay = calculate_backoff(
            attempt=100,
            base_delay=1.0,
            max_delay=max_d,
            jitter_factor=0,
        )
        assert delay <= max_d

    def test_jitter_adds_randomness(self):
        """Verify that jitter adds a random amount to the delay."""
        base = 1.0
        # Run multiple times to ensure variability
        delays = [
            calculate_backoff(0, base_delay=base, jitter_factor=0.5)
            for _ in range(10)
        ]
        # All should be >= base (since jitter is positive)
        assert all(d >= base for d in delays)
        # And not all should be identical (unless jitter is 0, but we set 0.5)
        # Due to randomness, it's highly likely they differ
        assert len(set(delays)) > 1


class TestRetryDecorator:
    @pytest.mark.parametrize("exc_type", RETRYABLE_EXCEPTIONS)
    def test_retry_on_retryable_exception(self, exc_type):
        """Verify that the function is retried on retryable exceptions."""
        call_count = 0
        max_calls = 3

        @retry_with_backoff(max_retries=5, exceptions=(exc_type,))
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < max_calls:
                raise exc_type("Simulated failure")
            return "success"

        # Mock time.sleep to speed up tests
        with patch("utils.retry.time.sleep"):
            result = flaky_func()
            assert result == "success"
            assert call_count == max_calls

    def test_raises_after_max_retries(self):
        """Verify that the original exception is raised after max retries."""
        call_count = 0

        @retry_with_backoff(max_retries=2, exceptions=(RequestException,))
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise RequestException("Persistent failure")

        with patch("utils.retry.time.sleep"):
            with pytest.raises(RequestException):
                always_fails()
            assert call_count == 3  # Initial + 2 retries

    def test_no_retry_on_non_retryable_exception(self):
        """Verify that non-retryable exceptions are not retried."""
        call_count = 0

        @retry_with_backoff(max_retries=5, exceptions=(RequestException,))
        def fails_with_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Non-retryable error")

        with patch("utils.retry.time.sleep"):
            with pytest.raises(ValueError):
                fails_with_value_error()
            assert call_count == 1  # Only initial call


class TestRetryCall:
    def test_retry_call_success(self):
        """Verify retry_call works for successful functions."""
        def success_func():
            return "done"

        result = retry_call(success_func, max_retries=3)
        assert result == "done"

    def test_retry_call_with_failure_then_success(self):
        """Verify retry_call retries on failure."""
        call_count = 0

        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Timeout("Transient timeout")
            return "recovered"

        with patch("utils.retry.time.sleep"):
            result = retry_call(
                flaky_func,
                max_retries=5,
                exceptions=(Timeout,),
            )
            assert result == "recovered"
            assert call_count == 2

    def test_retry_call_raises_after_max(self):
        """Verify retry_call raises after exhausting retries."""
        def always_fail():
            raise ConnectionError("Network down")

        with patch("utils.retry.time.sleep"):
            with pytest.raises(ConnectionError):
                retry_call(always_fail, max_retries=2, exceptions=(ConnectionError,))