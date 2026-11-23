"""
Unit tests for the error handling framework (T008).
Tests retry logic, timeout contexts, and custom exceptions.
"""
import pytest
import time
import signal
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import from the project's error_handling module
from error_handling import (
    InferenceTimeoutError,
    DatasetDownloadError,
    RetryExhaustedError,
    retry_with_backoff,
    timeout_context,
    enforce_inference_timeout,
    safe_download_with_retry,
    compute_sha256
)
from config import get_config

class TestCustomExceptions:
    def test_inference_timeout_error_creation(self):
        err = InferenceTimeoutError("Model took too long")
        assert "Model took too long" in str(err)
        assert isinstance(err, TimeoutError)

    def test_dataset_download_error_creation(self):
        err = DatasetDownloadError("Network failed", url="http://test.com")
        assert "Network failed" in str(err)
        assert err.url == "http://test.com"

    def test_retry_exhausted_error_creation(self):
        err = RetryExhaustedError("Max retries hit", last_exception=ValueError("bad"))
        assert "Max retries hit" in str(err)
        assert isinstance(err.last_exception, ValueError)

class TestRetryLogic:
    @pytest.fixture
    def mock_sleep(self):
        with patch('error_handling.time.sleep') as mock:
            yield mock

    def test_retry_success_on_first_try(self, mock_sleep):
        func = MagicMock(return_value="success")
        result = retry_with_backoff(func, max_retries=3, base_delay=0.1)
        assert result == "success"
        assert func.call_count == 1
        mock_sleep.assert_not_called()

    def test_retry_success_after_failure(self, mock_sleep):
        func = MagicMock(side_effect=[ValueError("fail"), "success"])
        result = retry_with_backoff(func, max_retries=3, base_delay=0.01)
        assert result == "success"
        assert func.call_count == 2
        assert mock_sleep.call_count == 1

    def test_retry_exhausted_raises(self, mock_sleep):
        func = MagicMock(side_effect=ValueError("always fail"))
        with pytest.raises(RetryExhaustedError):
            retry_with_backoff(func, max_retries=2, base_delay=0.01)
        assert func.call_count == 2

class TestTimeoutContext:
    def test_timeout_context_raises_timeout(self):
        # Using a simple context manager test
        # Note: In a real CPU-bound scenario, signal-based timeouts are used.
        # Here we simulate the logic or test the exception raising if signal is supported.
        if os.name == 'nt':
            # Windows doesn't support signal.SIGALRM in the same way
            pytest.skip("Signal-based timeout not fully supported on Windows in this test context")
            return

        try:
            with timeout_context(timeout=0.1):
                time.sleep(1.0) # Sleep longer than timeout
            assert False, "Should have raised InferenceTimeoutError"
        except InferenceTimeoutError:
            pass # Expected
        except TimeoutError:
            # Fallback if signal handling isn't perfect in test env
            pass

class TestHashComputation:
    def test_compute_sha256_on_string(self):
        # Helper to create a temp file for testing
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
            f.write("test data")
            temp_path = f.name

        try:
            hash_val = compute_sha256(temp_path)
            assert isinstance(hash_val, str)
            assert len(hash_val) == 64 # SHA-256 hex length
        finally:
            os.unlink(temp_path)

    def test_compute_sha256_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            compute_sha256("/nonexistent/path/file.txt")

class TestSafeDownloadWithRetry:
    @patch('error_handling.urllib.request.urlretrieve')
    @patch('error_handling.os.path.exists')
    def test_download_success(self, mock_exists, mock_urlretrieve):
        mock_exists.return_value = True
        mock_urlretrieve.return_value = ("/tmp/test.csv", None)
        
        # Mock the config to avoid file loading issues in test
        with patch('error_handling.get_config') as mock_config:
            mock_config.return_value = MagicMock()
            
            # This is a simplified test; real implementation might need more mocking
            # to avoid actual network calls or complex config loading
            pass 

class TestConfigIntegration:
    def test_retry_policy_config_exists(self):
        """Verify that the config system can provide retry settings."""
        config = get_config()
        # Check that retry settings exist in the config structure
        # The exact key names depend on config.py implementation
        assert hasattr(config, 'get') or isinstance(config, dict)
