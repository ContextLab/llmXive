import time
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from utils import (
    retry_with_exponential_backoff,
    calculate_backoff_delay,
    is_rate_limit_error,
    safe_call_with_retry
)

class TestRetryDecorator:
    def test_success_on_first_attempt(self):
        @retry_with_exponential_backoff(max_retries=3)
        def success_func():
            return "success"
        
        result = success_func()
        assert result == "success"

    def test_retry_on_failure_then_success(self):
        call_count = 0
        
        @retry_with_exponential_backoff(max_retries=3, base_delay=0.01, jitter=False)
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"
        
        result = flaky_func()
        assert result == "success"
        assert call_count == 3

    def test_max_retries_exceeded(self):
        @retry_with_exponential_backoff(max_retries=2, base_delay=0.01, jitter=False)
        def always_fails():
            raise ValueError("Permanent error")
        
        with pytest.raises(ValueError):
            always_fails()

    def test_exponential_backoff_timing(self):
        start_time = time.time()
        
        @retry_with_exponential_backoff(max_retries=2, base_delay=0.1, max_delay=1.0, jitter=False)
        def slow_fail():
            raise ValueError("Error")
        
        with pytest.raises(ValueError):
            slow_fail()
        
        elapsed = time.time() - start_time
        # Should have waited at least base_delay + (base_delay * 2) = 0.3s
        assert elapsed >= 0.25  # Allow small tolerance

class TestCalculateBackoffDelay:
    def test_first_attempt_delay(self):
        delay = calculate_backoff_delay(attempt=0, base_delay=2.0, jitter=False)
        assert delay == 2.0

    def test_exponential_growth(self):
        delay0 = calculate_backoff_delay(attempt=0, base_delay=2.0, jitter=False)
        delay1 = calculate_backoff_delay(attempt=1, base_delay=2.0, jitter=False)
        delay2 = calculate_backoff_delay(attempt=2, base_delay=2.0, jitter=False)
        
        assert delay0 == 2.0
        assert delay1 == 4.0
        assert delay2 == 8.0

    def test_max_delay_cap(self):
        delay = calculate_backoff_delay(
            attempt=10, base_delay=2.0, max_delay=10.0, jitter=False
        )
        assert delay == 10.0

    def test_jitter_in_range(self):
        # With jitter, delay should be between 50% and 150% of base
        base = 10.0
        for _ in range(100):
            delay = calculate_backoff_delay(attempt=0, base_delay=base, jitter=True)
            assert 0.5 * base <= delay <= 1.5 * base

class TestIsRateLimitError:
    def test_429_error(self):
        assert is_rate_limit_error(Exception("429 Too Many Requests")) is True

    def test_rate_limit_keyword(self):
        assert is_rate_limit_error(Exception("Rate limit exceeded")) is True

    def test_non_rate_limit_error(self):
        assert is_rate_limit_error(Exception("Connection failed")) is False

    def test_case_insensitive(self):
        assert is_rate_limit_error(Exception("TOO MANY REQUESTS")) is True

class TestSafeCallWithRetry:
    def test_success(self):
        def success_func():
            return "result"
        
        result = safe_call_with_retry(success_func)
        assert result == "result"

    def test_failure_with_rate_limit_retry(self):
        call_count = 0
        
        def rate_limited_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("429 Too Many Requests")
            return "success"
        
        result = safe_call_with_retry(rate_limited_func, max_retries=3, base_delay=0.01, jitter=False)
        assert result == "success"
        assert call_count == 3

    def test_non_rate_limit_no_retry(self):
        call_count = 0
        
        def non_retryable_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Non-retryable error")
        
        with pytest.raises(ValueError):
            safe_call_with_retry(non_retryable_func, check_rate_limit=True)
        
        # Should only be called once since it's not a rate limit error
        assert call_count == 1

    def test_max_retries_exceeded_returns_none(self):
        def always_fails():
            raise Exception("429 Too Many Requests")
        
        result = safe_call_with_retry(always_fails, max_retries=2, base_delay=0.01, jitter=False)
        assert result is None