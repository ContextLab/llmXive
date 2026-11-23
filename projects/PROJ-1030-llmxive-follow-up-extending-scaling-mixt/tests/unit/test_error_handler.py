import pytest
import time
from unittest.mock import patch, MagicMock
from utils.error_handler import DataFetchError, ConfigError, PhysicsSimError, retry_with_backoff
from utils.logging_config import get_logger

class TestRetryWithBackoff:
    """Tests for the retry_with_backoff decorator."""

    def test_success_on_first_attempt(self):
        """Test that a successful function returns immediately."""
        @retry_with_backoff(max_retries=3)
        def success_func():
            return "success"
        
        result = success_func()
        assert result == "success"

    def test_retry_on_transient_error(self):
        """Test that transient errors trigger retries."""
        call_count = 0
        
        @retry_with_backoff(max_retries=3, initial_delay=0.01, max_delay=0.01)
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary network issue")
            return "success after retries"
        
        result = flaky_func()
        assert result == "success after retries"
        assert call_count == 3

    def test_fail_loudly_after_max_retries(self):
        """Test that function fails loudly after max retries."""
        @retry_with_backoff(max_retries=2, initial_delay=0.01, max_delay=0.01)
        def always_fails():
            raise ConnectionError("Persistent failure")
        
        with pytest.raises(SystemExit):
            always_fails()

    def test_non_retryable_exception(self):
        """Test that non-retryable exceptions are not retried."""
        @retry_with_backoff(
            max_retries=3, 
            retryable_exceptions=[ValueError],
            initial_delay=0.01, 
            max_delay=0.01
        )
        def raises_type_error():
            raise TypeError("Not retryable")
        
        with pytest.raises(SystemExit):
            raises_type_error()

class TestCustomExceptions:
    """Tests for custom exception classes."""

    def test_data_fetch_error(self):
        """Test DataFetchError instantiation."""
        error = DataFetchError("Failed to fetch data")
        assert str(error) == "Failed to fetch data"

    def test_config_error(self):
        """Test ConfigError instantiation."""
        error = ConfigError("Invalid configuration")
        assert str(error) == "Invalid configuration"

    def test_physics_sim_error(self):
        """Test PhysicsSimError instantiation."""
        error = PhysicsSimError("Simulation failed")
        assert str(error) == "Simulation failed"

class TestFailLoudly:
    """Tests for the fail_loudly mechanism."""

    def test_fail_loudly_exits(self):
        """Test that fail_loudly causes system exit."""
        logger = get_logger("test")
        
        with pytest.raises(SystemExit) as exc_info:
            from utils.logging_config import fail_loudly
            fail_loudly(logger, "Test fatal error")
        
        assert exc_info.value.code == 1

    def test_fail_loudly_with_exception(self):
        """Test that fail_loudly includes exception details."""
        logger = get_logger("test")
        
        with pytest.raises(SystemExit) as exc_info:
            from utils.logging_config import fail_loudly
            test_exception = ValueError("Test error")
            fail_loudly(logger, "Test error", test_exception)
        
        assert exc_info.value.code == 1
