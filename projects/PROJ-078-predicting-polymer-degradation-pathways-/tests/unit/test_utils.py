"""
Unit tests for utility functions.
"""
import pytest
import time
from utils import retry_with_backoff, get_logger, get_project_paths
from pathlib import Path

class TestRetryWithBackoff:
    def test_retry_succeeds_on_first_attempt(self):
        """Test that a successful function returns immediately."""
        call_count = 0
        @retry_with_backoff(max_retries=3)
        def success_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = success_func()
        assert result == "success"
        assert call_count == 1

    def test_retry_succeeds_after_failure(self):
        """Test that a function succeeds after some failures."""
        call_count = 0
        @retry_with_backoff(max_retries=3)
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Rate limit")
            return "success"

        result = flaky_func()
        assert result == "success"
        assert call_count == 2

    def test_retry_exhausts_retries(self):
        """Test that a function raises after max retries."""
        call_count = 0
        @retry_with_backoff(max_retries=2)
        def always_fail():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")

        with pytest.raises(ValueError):
            always_fail()
        assert call_count == 3  # Initial + 2 retries

def test_get_project_paths():
    """Test that project paths are returned correctly."""
    paths = get_project_paths()
    assert "code" in paths
    assert "data" in paths
    assert "tests" in paths
    assert "state" in paths
