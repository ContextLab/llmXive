import pytest
import time
from unittest.mock import patch, MagicMock
import hashlib
from pathlib import Path

from code.utils import exponential_backoff_retry, calculate_checksum, log_api_provenance

class TestUtils:
    """Unit tests for utility functions."""

    def test_exponential_backoff_retry_success(self):
        """Test retry logic on successful function."""
        def mock_func():
            return "success"
        
        result = exponential_backoff_retry(mock_func)
        assert result == "success"

    def test_exponential_backoff_retry_failure(self):
        """Test retry logic when function eventually succeeds."""
        call_count = 0
        
        def mock_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Rate limit")
            return "success"
        
        result = exponential_backoff_retry(mock_func, max_retries=5, backoff_factor=0.1)
        assert result == "success"
        assert call_count == 3

    def test_exponential_backoff_retry_max_exceeded(self):
        """Test that exception is raised after max retries."""
        def mock_func():
            raise Exception("Always fails")
        
        with pytest.raises(Exception):
            exponential_backoff_retry(mock_func, max_retries=3, backoff_factor=0.1)

    def test_calculate_checksum(self):
        """Test checksum calculation."""
        # Create a temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        checksum = calculate_checksum(temp_path)
        
        # Verify it's a valid SHA256 hash
        assert len(checksum) == 64
        assert all(c in '0123456789abcdef' for c in checksum)
        
        # Clean up
        Path(temp_path).unlink()

    def test_log_api_provenance(self):
        """Test API provenance logging."""
        import json
        from code import config
        
        # Ensure log directory exists
        Path(config.DATA_LOGS_DIR).mkdir(parents=True, exist_ok=True)
        
        log_api_provenance(
            operation="test_op",
            status="success",
            details={"key": "value"},
            output_path="/tmp/test.csv"
        )
        
        # Read the log file and verify
        log_file = Path(config.DATA_LOGS_DIR) / "api_log.jsonl"
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) >= 1
        last_entry = json.loads(lines[-1])
        assert last_entry['operation'] == 'test_op'
        assert last_entry['status'] == 'success'
        assert last_entry['details'] == {"key": "value"}