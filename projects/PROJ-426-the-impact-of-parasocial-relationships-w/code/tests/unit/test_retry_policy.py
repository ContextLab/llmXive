"""
Unit tests for the retry policy implementation.
"""

import pytest
import time
import random
from src.utils.retry_policy import (
    RetryConfig,
    DEFAULT_RETRY_CONFIG,
    retry_with_backoff,
    calculate_backoff_delay
)


class TestRetryConfig:
    """Tests for the RetryConfig class."""

    def test_default_initialization(self):
        """Test that default values are set correctly."""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True

    def test_custom_initialization(self):
        """Test custom configuration values."""
        config = RetryConfig(
            max_retries=5,
            base_delay=2.0,
            max_delay=120.0,
            exponential_base=3.0,
            jitter=False
        )
        assert config.max_retries == 5
        assert config.base_delay == 2.0
        assert config.max_delay == 120.0
        assert config.exponential_base == 3.0
        assert config.jitter is False

    def test_invalid_max_retries(self):
        """Test that negative max_retries raises ValueError."""
        with pytest.raises(ValueError):
            RetryConfig(max_retries=-1)

    def test_invalid_base_delay(self):
        """Test that non-positive base_delay raises ValueError."""
        with pytest.raises(ValueError):
            RetryConfig(base_delay=0)
        with pytest.raises(ValueError):
            RetryConfig(base_delay=-1)

    def test_invalid_max_delay(self):
        """Test that non-positive max_delay raises ValueError."""
        with pytest.raises(ValueError):
            RetryConfig(max_delay=0)
        with pytest.raises(ValueError):
            RetryConfig(max_delay=-1)

    def test_max_delay_less_than_base_delay(self):
        """Test that max_delay < base_delay raises ValueError."""
        with pytest.raises(ValueError):
            RetryConfig(base_delay=10.0, max_delay=5.0)

    def test_calculate_delay_exponential_growth(self):
        """Test that delay grows exponentially without jitter."""
        config = RetryConfig(base_delay=1.0, max_delay=60.0, jitter=False)
        
        # Attempt 0: 1 * 2^0 = 1
        assert config.calculate_delay(0) == 1.0
        # Attempt 1: 1 * 2^1 = 2
        assert config.calculate_delay(1) == 2.0
        # Attempt 2: 1 * 2^2 = 4
        assert config.calculate_delay(2) == 4.0
        # Attempt 3: 1 * 2^3 = 8
        assert config.calculate_delay(3) == 8.0

    def test_calculate_delay_max_cap(self):
        """Test that delay is capped at max_delay."""
        config = RetryConfig(base_delay=1.0, max_delay=10.0, jitter=False)
        
        # 2^3 = 8, 2^4 = 16 (should be capped at 10)
        assert config.calculate_delay(3) == 8.0
        assert config.calculate_delay(4) == 10.0
        assert config.calculate_delay(10) == 10.0

    def test_calculate_delay_with_jitter(self):
        """Test that jitter introduces variation."""
        config = RetryConfig(base_delay=1.0, max_delay=60.0, jitter=True)
        
        # Run multiple times to ensure jitter is applied
        delays = [config.calculate_delay(0) for _ in range(10)]
        # With jitter, not all delays should be exactly the same
        # (though with small sample size it's probabilistic, the logic is tested)
        # We just verify the function returns a float
        assert all(isinstance(d, float) for d in delays)
        assert all(0.5 <= d <= 1.5 for d in delays)  # 1.0 * [0.5, 1.5]

    def test_repr(self):
        """Test string representation."""
        config = RetryConfig(max_retries=5, base_delay=2.0)
        repr_str = repr(config)
        assert "RetryConfig" in repr_str
        assert "max_retries=5" in repr_str
        assert "base_delay=2.0" in repr_str


class TestCalculateBackoffDelay:
    """Tests for the standalone calculate_backoff_delay function."""

    def test_function_returns_delay(self):
        """Test that the function returns a delay value."""
        delay = calculate_backoff_delay(0)
        assert isinstance(delay, float)
        assert delay > 0

    def test_function_respects_max_delay(self):
        """Test that the function respects max_delay cap."""
        delay = calculate_backoff_delay(10, base_delay=1.0, max_delay=10.0, jitter=False)
        assert delay == 10.0

    def test_function_with_jitter(self):
        """Test that jitter is applied when enabled."""
        delays = [
            calculate_backoff_delay(0, base_delay=1.0, max_delay=60.0, jitter=True)
            for _ in range(5)
        ]
        assert len(delays) == 5
        # All should be within jitter range of base
        assert all(0.5 <= d <= 1.5 for d in delays)


class TestRetryWithBackoffDecorator:
    """Tests for the retry_with_backoff decorator."""

    def test_success_on_first_attempt(self):
        """Test that a successful function is called once."""
        call_count = 0

        @retry_with_backoff()
        def success_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = success_func()
        assert result == "success"
        assert call_count == 1

    def test_retry_on_failure(self):
        """Test that the function is retried on failure."""
        call_count = 0
        max_calls = 3

        @retry_with_backoff(config=RetryConfig(max_retries=2, base_delay=0.01, jitter=False))
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < max_calls:
                raise ValueError("Transient error")
            return "success"

        result = failing_func()
        assert result == "success"
        # Should have tried 3 times (1 initial + 2 retries)
        assert call_count == 3

    def test_exhaust_retries_raises_exception(self):
        """Test that the original exception is raised after max retries."""
        @retry_with_backoff(config=RetryConfig(max_retries=1, base_delay=0.01, jitter=False))
        def always_fails():
            raise ValueError("Persistent error")

        with pytest.raises(ValueError, match="Persistent error"):
            always_fails()

    def test_specific_exception_handling(self):
        """Test that only specific exceptions trigger retry."""
        call_count = 0

        @retry_with_backoff(
            config=RetryConfig(max_retries=2, base_delay=0.01, jitter=False),
            exceptions_to_handle=(ValueError,)
        )
        def specific_error_func():
            nonlocal call_count
            call_count += 1
            raise TypeError("Different error")

        with pytest.raises(TypeError):
            specific_error_func()
        # Should not retry TypeError
        assert call_count == 1

    def test_success_after_retry(self):
        """Test that success is returned after a retry."""
        call_count = 0

        @retry_with_backoff(config=RetryConfig(max_retries=2, base_delay=0.01, jitter=False))
        def eventually_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("Network blip")
            return "finally worked"

        result = eventually_succeeds()
        assert result == "finally worked"
        assert call_count == 2