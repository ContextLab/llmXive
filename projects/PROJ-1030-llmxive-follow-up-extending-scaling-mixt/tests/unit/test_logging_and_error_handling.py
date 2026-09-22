import pytest
import logging
import sys
from io import StringIO
from pathlib import Path
import tempfile
import os

# Import the modules under test
from utils.logging_config import configure_root_logger, get_logger, fail_loudly, DataFetchLogger
from utils.error_handler import DataFetchError, retry_with_backoff, DataFetchHandler

class TestLoggingConfig:
    def test_configure_root_logger_creates_handlers(self):
        # Use a temporary directory for logs if needed, but configure_root_logger
        # creates a 'logs' dir by default. We just check it doesn't crash.
        configure_root_logger("DEBUG")
        logger = logging.getLogger()
        assert len(logger.handlers) > 0
    
    def test_get_logger_returns_named_logger(self):
        configure_root_logger("INFO")
        logger = get_logger("test_unit")
        assert logger.name == "test_unit"
        assert isinstance(logger, logging.Logger)
    
    def test_data_fetch_logger_formatting(self):
        configure_root_logger("INFO")
        fetch_logger = DataFetchLogger("TestFetch")
        assert fetch_logger.logger.name == "DataFetch" or "DataFetch" in fetch_logger.logger.name
        
        # Check that methods exist and don't crash
        fetch_logger.info("Info message")
        fetch_logger.warning("Warning message")
        fetch_logger.error("Error message")
        fetch_logger.debug("Debug message")

class TestFailLoudly:
    def test_fail_loudly_raises_runtime_error(self):
        with pytest.raises(RuntimeError) as exc_info:
            fail_loudly("Test fatal error")
        assert "Test fatal error" in str(exc_info.value)
    
    def test_fail_loudly_includes_exception(self):
        try:
            1 / 0
        except ZeroDivisionError as e:
            with pytest.raises(RuntimeError) as exc_info:
                fail_loudly("Division failed", exception=e)
            assert "Division failed" in str(exc_info.value)
            assert "ZeroDivisionError" in str(exc_info.value)

class TestRetryWithBackoff:
    @pytest.mark.parametrize("max_retries, should_fail", [(1, True), (3, False)])
    def test_retry_mechanism(self, max_retries, should_fail):
        attempt_count = 0
        
        @retry_with_backoff(max_retries=max_retries, base_delay=0.01)
        def flaky_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ConnectionError("Transient error")
            return "Success"
        
        if should_fail:
            # With max_retries=1, it should fail immediately after 1 attempt
            # But our logic in retry_with_backoff calls fail_loudly which raises RuntimeError
            # So we expect RuntimeError here if max_retries is reached and it still fails.
            # However, the decorator logic in error_handler.py calls fail_loudly on last retry.
            # Let's adjust the test to match the implementation behavior.
            # If max_retries=1, it tries once, fails, retries 0 times (loop ends), then calls fail_loudly.
            # Wait, loop is range(1, max_retries + 1). If max=1, loop runs for attempt=1.
            # If it fails, and attempt == max_retries, it calls fail_loudly.
            # So it raises RuntimeError.
            with pytest.raises(RuntimeError):
                flaky_function()
            assert attempt_count == 1
        else:
            # max_retries=3, function succeeds on 3rd attempt
            result = flaky_function()
            assert result == "Success"
            assert attempt_count == 3
    
    def test_retry_with_custom_exception(self):
        attempt_count = 0
        
        @retry_with_backoff(max_retries=2, base_delay=0.01, exceptions=[ValueError])
        def raises_value_error():
            nonlocal attempt_count
            attempt_count += 1
            raise ValueError("Custom error")
        
        with pytest.raises(RuntimeError): # Because fail_loudly is called
            raises_value_error()
        assert attempt_count == 2

class TestDataFetchHandler:
    def test_fetch_success(self):
        handler = DataFetchHandler()
        def success_func():
            return "Data"
        
        result = handler.fetch_with_retry(success_func, "test_resource", max_retries=1)
        assert result == "Data"
    
    def test_fetch_failure_loud(self):
        handler = DataFetchHandler()
        def fail_func():
            raise DataFetchError("Fetch failed")
        
        with pytest.raises(RuntimeError):
            handler.fetch_with_retry(fail_func, "test_resource", max_retries=1)
