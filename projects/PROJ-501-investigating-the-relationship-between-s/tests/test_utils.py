"""
Unit tests for utils.py functions.
Tests API retry logic with mock rate limit responses.
"""
import pytest
import time
from unittest.mock import Mock, patch
from pathlib import Path
import sys

# Ensure code directory is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils import exponential_backoff_retry


class TestExponentialBackoffRetry:
    """Tests for exponential_backoff_retry function."""

    def test_retry_on_rate_limit(self):
        """Test that function retries on rate limit responses."""
        call_count = 0
        
        def mock_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                # Simulate rate limit on first two attempts
                raise Exception("429 Too Many Requests")
            return "success"
        
        # Apply retry decorator
        retry_func = exponential_backoff_retry(mock_function, max_retries=5, base_delay=0.1)
        
        # Should succeed after retries
        result = retry_func()
        
        assert result == "success", "Should eventually succeed"
        assert call_count == 3, "Should have made 3 attempts (2 failures + 1 success)"

    def test_max_retries_exceeded(self):
        """Test that function raises after max retries exceeded."""
        def mock_function():
            raise Exception("429 Too Many Requests")
        
        retry_func = exponential_backoff_retry(mock_function, max_retries=2, base_delay=0.1)
        
        # Should raise exception after max retries
        with pytest.raises(Exception) as exc_info:
            retry_func()
        
        assert "429 Too Many Requests" in str(exc_info.value)

    def test_no_retry_on_success(self):
        """Test that function doesn't retry on successful response."""
        call_count = 0
        
        def mock_function():
            nonlocal call_count
            call_count += 1
            return "success"
        
        retry_func = exponential_backoff_retry(mock_function, max_retries=5, base_delay=0.1)
        
        result = retry_func()
        
        assert result == "success"
        assert call_count == 1, "Should have made only 1 attempt"

    def test_retry_with_different_error_types(self):
        """Test retry behavior with different error types."""
        call_count = 0
        
        def mock_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Connection refused")
            return "success"
        
        retry_func = exponential_backoff_retry(mock_function, max_retries=3, base_delay=0.1)
        
        result = retry_func()
        
        assert result == "success"
        assert call_count == 2, "Should have retried once"

    def test_backoff_delay_timing(self):
        """Test that backoff delay increases between retries."""
        call_times = []
        
        def mock_function():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise Exception("Rate limited")
            return "success"
        
        retry_func = exponential_backoff_retry(mock_function, max_retries=5, base_delay=0.1)
        
        result = retry_func()
        
        assert result == "success"
        
        # Check that delays increased
        if len(call_times) >= 3:
            delay1 = call_times[1] - call_times[0]
            delay2 = call_times[2] - call_times[1]
            
            # Second delay should be at least as long as first (exponential backoff)
            assert delay2 >= delay1 * 0.9, "Backoff delay should increase"
