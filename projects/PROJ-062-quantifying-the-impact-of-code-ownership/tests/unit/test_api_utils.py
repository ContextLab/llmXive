"""
Unit tests for API utilities, specifically exponential backoff logic.
"""
import time
import pytest
from unittest.mock import patch, MagicMock

from utils.api_utils import (
    exponential_backoff_delay,
    retry_with_exponential_backoff,
    fetch_with_backoff,
    MAX_RETRIES,
    MIN_DELAY_SECONDS
)


class TestExponentialBackoffDelay:
    """Tests for the exponential_backoff_delay function."""

    def test_delay_increases_with_attempt(self):
        """Delay should increase as attempt number increases."""
        delay_0 = exponential_backoff_delay(attempt=0, min_delay=60)
        delay_1 = exponential_backoff_delay(attempt=1, min_delay=60)
        delay_2 = exponential_backoff_delay(attempt=2, min_delay=60)

        assert delay_0 >= 60
        assert delay_1 >= 60
        assert delay_2 >= 60
        # Due to jitter, we can't guarantee strict ordering every time,
        # but on average it should increase. We'll check the expected base.
        # Base without jitter: 60, 120, 240
        # With jitter range [0.5, 1.5], we check bounds.
        assert delay_0 <= 60 * 1.5
        assert delay_2 <= (60 * 4) * 1.5  # 240 * 1.5

    def test_delay_respects_max_limit(self):
        """Delay should not exceed max_delay."""
        large_attempt = 10
        delay = exponential_backoff_delay(
            attempt=large_attempt,
            min_delay=60,
            max_delay=300
        )
        assert delay <= 300

    def test_min_delay_parameter(self):
        """Function should respect custom min_delay."""
        delay = exponential_backoff_delay(attempt=0, min_delay=10)
        assert delay >= 10
        assert delay <= 10 * 1.5  # Max with jitter


class TestRetryDecorator:
    """Tests for the retry_with_exponential_backoff decorator."""

    @pytest.fixture
    def mock_time_sleep(self):
        """Mock time.sleep to speed up tests."""
        with patch('utils.api_utils.time.sleep') as mock_sleep:
            yield mock_sleep

    def test_successful_call_no_retry(self, mock_time_sleep):
        """If function succeeds on first try, no retry should occur."""
        @retry_with_exponential_backoff(max_retries=3)
        def success_func():
            return "success"

        result = success_func()
        assert result == "success"
        mock_time_sleep.assert_not_called()

    def test_retry_on_failure(self, mock_time_sleep):
        """Function should retry on failure up to max_retries."""
        call_count = 0

        @retry_with_exponential_backoff(max_retries=3, min_delay=0.01)
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Transient error")
            return "success"

        result = flaky_func()
        assert result == "success"
        assert call_count == 3
        # Should have slept 2 times (after attempt 1 and 2)
        assert mock_time_sleep.call_count == 2

    def test_exhaust_retries_raises(self, mock_time_sleep):
        """Should raise exception after exhausting retries."""
        @retry_with_exponential_backoff(max_retries=2, min_delay=0.01)
        def failing_func():
            raise ValueError("Persistent error")

        with pytest.raises(ValueError, match="Persistent error"):
            failing_func()

        # Should have retried 2 times (total 3 calls: 1 initial + 2 retries)
        assert mock_time_sleep.call_count == 2


class TestFetchWithBackoff:
    """Tests for the fetch_with_backoff function."""

    @pytest.fixture
    def mock_time_sleep(self):
        with patch('utils.api_utils.time.sleep') as mock_sleep:
            yield mock_sleep

    def test_successful_execution(self, mock_time_sleep):
        """Should return result on success without retrying."""
        def success_func():
            return "data"

        result = fetch_with_backoff(success_func, max_retries=3)
        assert result == "data"
        mock_time_sleep.assert_not_called()

    def test_retry_then_success(self, mock_time_sleep):
        """Should retry and eventually return result."""
        call_count = 0

        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Network issue")
            return "data"

        result = fetch_with_backoff(flaky_func, max_retries=3, min_delay=0.01)
        assert result == "data"
        assert call_count == 2
        assert mock_time_sleep.call_count == 1

    def test_exhaust_retries_raises(self, mock_time_sleep):
        """Should raise after max retries."""
        def failing_func():
            raise RuntimeError("Always fails")

        with pytest.raises(RuntimeError, match="Always fails"):
            fetch_with_backoff(failing_func, max_retries=2, min_delay=0.01)

        assert mock_time_sleep.call_count == 2