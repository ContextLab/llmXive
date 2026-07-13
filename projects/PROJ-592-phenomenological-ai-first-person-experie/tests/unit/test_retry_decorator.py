"""Tests for the retry_on_failure decorator with various call signatures."""
import pytest
import time
from unittest.mock import patch, MagicMock

from utils.logging import retry_on_failure, get_logger


class TestRetryDecorator:
    """Test cases for the retry_on_failure decorator."""

    def test_max_retries_with_logger(self):
        """Test @retry_on_failure(max_retries=N, logger=lg) signature."""
        logger = get_logger()
        call_count = 0

        @retry_on_failure(max_retries=3, logger=logger)
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Transient error")
            return "success"

        result = flaky_function()
        assert result == "success"
        assert call_count == 3

    def test_max_attempts_with_delay(self):
        """Test @retry_on_failure(max_attempts=N, delay=S) signature."""
        call_count = 0

        @retry_on_failure(max_attempts=3, delay=0.1)
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Transient error")
            return "success"

        result = flaky_function()
        assert result == "success"
        assert call_count == 2

    def test_max_attempts_with_delay_seconds(self):
        """Test @retry_on_failure(max_attempts=N, delay_seconds=S) signature."""
        call_count = 0

        @retry_on_failure(max_attempts=3, delay_seconds=0.1)
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Transient error")
            return "success"

        result = flaky_function()
        assert result == "success"
        assert call_count == 2

    def test_exhaust_retries(self):
        """Test that exception is raised after all retries exhausted."""
        @retry_on_failure(max_retries=2)
        def always_fails():
            raise ValueError("Always fails")

        with pytest.raises(ValueError, match="Always fails"):
            always_fails()

    def test_defaults(self):
        """Test default values when no arguments provided."""
        call_count = 0

        @retry_on_failure()
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Transient error")
            return "success"

        result = flaky_function()
        assert result == "success"
        # Default is 3 attempts
        assert call_count == 2

    def test_successful_first_try(self):
        """Test that successful first try does not retry."""
        call_count = 0

        @retry_on_failure(max_retries=5)
        def success_first():
            nonlocal call_count
            call_count += 1
            return "success"

        result = success_first()
        assert result == "success"
        assert call_count == 1
