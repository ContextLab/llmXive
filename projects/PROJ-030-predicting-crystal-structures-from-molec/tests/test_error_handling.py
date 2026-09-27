"""
Tests for the error handling framework (T007).

These tests verify that:
1. DownloadError is raised explicitly on network failures.
2. MemoryErrorHandled is raised on memory constraints.
3. No synthetic data is returned as a fallback.
"""

import pytest
from unittest.mock import patch, MagicMock

# Import the module under test
from code.exceptions import DownloadError, MemoryErrorHandled, ValidationError
from code.error_handling import (
    handle_download_failure,
    handle_memory_error,
    safe_download,
    safe_process_item
)
from code.logging_config import get_logger

logger = get_logger(__name__)

class TestDownloadErrorHandling:
    """Tests for DownloadError handling."""
    
    def test_handle_download_failure_raises_download_error(self):
        """Verify that network errors are converted to DownloadError."""
        
        @handle_download_failure
        def failing_download(source: str):
            raise ConnectionError("Network unreachable")
        
        with pytest.raises(DownloadError) as exc_info:
            failing_download("https://example.com/data")
        
        assert "Network unreachable" in str(exc_info.value)
        assert exc_info.value.source == "https://example.com/data"
    
    def test_handle_download_failure_catches_timeout(self):
        """Verify that timeouts are converted to DownloadError."""
        
        @handle_download_failure
        def timeout_download(source: str):
            raise TimeoutError("Request timed out")
        
        with pytest.raises(DownloadError) as exc_info:
            timeout_download("https://slow-server.com")
        
        assert "timed out" in str(exc_info.value)
    
    def test_safe_download_raises_on_failure(self):
        """Verify safe_download does not return synthetic data on failure."""
        
        def mock_fail(source: str):
            raise ConnectionError("Failed")
        
        with pytest.raises(DownloadError):
            safe_download(mock_fail, "fake-source")
        
        # Ensure no synthetic fallback occurred (the function should raise)
        # If it returned None or a mock object, the test would have passed incorrectly
    
    def test_safe_download_returns_data_on_success(self):
        """Verify safe_download returns data on success."""
        
        def mock_success(source: str):
            return {"data": "real_content"}
        
        result = safe_download(mock_success, "valid-source")
        assert result == {"data": "real_content"}

class TestMemoryErrorHandling:
    """Tests for MemoryError handling."""
    
    def test_handle_memory_error_raises_custom_exception(self):
        """Verify that MemoryError is caught and re-raised as MemoryErrorHandled."""
        
        @handle_memory_error
        def memory_intensive_process(item: dict):
            raise MemoryError("Out of RAM")
        
        with pytest.raises(MemoryErrorHandled) as exc_info:
            memory_intensive_process({"id": 123})
        
        assert "Out of RAM" in str(exc_info.value)
        assert "123" in str(exc_info.value)
    
    def test_safe_process_item_returns_none_on_memory_error(self):
        """Verify safe_process_item returns None and logs when memory error occurs."""
        
        def failing_process(item):
            raise MemoryError("OOM")
        
        result = safe_process_item(failing_process, {"id": 999}, item_id="999")
        assert result is None
        # The function should have logged a warning, but we can't easily check logs in unit tests
        # without complex mocking. The return value of None is the key indicator.
    
    def test_safe_process_item_raises_other_exceptions(self):
        """Verify safe_process_item propagates non-memory errors."""
        
        def failing_process(item):
            raise ValueError("Something else went wrong")
        
        with pytest.raises(ValueError):
            safe_process_item(failing_process, {"id": 1})

class TestNoSyntheticFallback:
    """
    Critical tests to ensure the 'fail loudly, never silently' principle is upheld.
    """
    
    def test_no_synthetic_fallback_in_download(self):
        """
        Verify that when a download fails, the system does NOT return a mock object
        or synthetic data. It MUST raise an exception.
        """
        
        def mock_download_fail(source: str):
            raise ConnectionError("Simulated failure")
        
        # This must raise, not return a dummy dict
        with pytest.raises(DownloadError):
            safe_download(mock_download_fail, "test-source")
        
        # If we reach here, the test failed (because it didn't raise)
        # But pytest.raises handles this. If the function returned a value instead of raising,
        # this block would not execute.
    
    def test_memory_error_does_not_generate_fake_data(self):
        """
        Verify that when a memory error occurs, the system does NOT generate
        a synthetic record to replace the missing one.
        """
        
        def mock_process(item):
            raise MemoryError("OOM")
        
        result = safe_process_item(mock_process, {"id": 1}, item_id="1")
        
        # The result must be None (skipped), not a fake dict
        assert result is None
        assert isinstance(result, type(None)) # Explicitly check it's not a dict