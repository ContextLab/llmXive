import time
import pytest
from unittest.mock import patch, MagicMock

from utils.retry import (
    calculate_delay,
    RetryConfig,
    retry_with_backoff,
    retry_request,
    DataFetchError
)

class TestCalculateDelay:
    def test_basic_exponential_backoff(self):
        config = RetryConfig(base_delay=1.0, exponential_base=2.0, jitter=False)
        # Attempt 0: 1 * 2^0 = 1
        assert calculate_delay(0, config) == 1.0
        # Attempt 1: 1 * 2^1 = 2
        assert calculate_delay(1, config) == 2.0
        # Attempt 2: 1 * 2^2 = 4
        assert calculate_delay(2, config) == 4.0

    def test_max_delay_cap(self):
        config = RetryConfig(base_delay=1.0, exponential_base=2.0, max_delay=5.0, jitter=False)
        # Attempt 3: 1 * 2^3 = 8, but capped at 5.0
        assert calculate_delay(3, config) == 5.0

    def test_jitter_adds_variance(self):
        config = RetryConfig(base_delay=1.0, exponential_base=1.0, jitter=True)
        # With base 1.0 and jitter, delay should be between 1.0 and 1.5
        for _ in range(10):
            delay = calculate_delay(0, config)
            assert 1.0 <= delay <= 1.5

class TestRetryWithBackoff:
    @pytest.mark.parametrize("max_retries, expected_calls", [
        (0, 1),
        (1, 2),
        (3, 4),
    ])
    def test_success_on_first_try(self, max_retries, expected_calls):
        config = RetryConfig(max_retries=max_retries)
        call_count = 0

        @retry_with_backoff(config)
        def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_func()
        assert result == "success"
        assert call_count == 1

    def test_retries_on_failure(self):
        config = RetryConfig(max_retries=3, base_delay=0.01, jitter=False)
        call_count = 0

        @retry_with_backoff(config)
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Simulated network error")
            return "success"

        result = flaky_func()
        assert result == "success"
        assert call_count == 3

    def test_raises_after_max_retries(self):
        config = RetryConfig(max_retries=2, base_delay=0.01, jitter=False)
        call_count = 0

        @retry_with_backoff(config)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Persistent error")

        with pytest.raises(DataFetchError):
            always_fails()

        assert call_count == 3  # Initial + 2 retries

    def test_raises_original_exception_if_not_network_error(self):
        config = RetryConfig(max_retries=1, base_delay=0.01, jitter=False)
        
        @retry_with_backoff(config)
        def value_error_func():
            raise ValueError("Not a network error")

        with pytest.raises(ValueError):
            value_error_func()

class TestRetryRequest:
    def test_convenience_wrapper(self):
        call_count = 0

        @retry_request(max_retries=2, base_delay=0.01, jitter=False)
        def network_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TimeoutError("Timeout")
            return "done"

        assert network_func() == "done"
        assert call_count == 2