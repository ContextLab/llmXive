"""
Unit tests for the utils module.

Tests cover:
- Logging configuration
- Checksum computation
- Error logging formatting
- Safe exit behavior
"""
import logging
import os
import tempfile
import pytest
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock

# Import the module under test
# Ensure we are importing from the code directory relative to tests
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
from utils import setup_logging, compute_checksum, log_error, safe_exit


class TestSetupLogging:
    def test_setup_logging_console_only(self, tmp_path):
        """Test that logging works with console only."""
        logger = setup_logging(log_level="DEBUG")
        assert logger.level == logging.DEBUG
        assert len(logger.root.handlers) >= 1  # At least console handler

    def test_setup_logging_with_file(self, tmp_path):
        """Test that logging creates a file handler when path is provided."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_level="INFO", log_file=str(log_file))
        
        assert log_file.exists()
        # Check that a file handler was added
        file_handlers = [h for h in logger.root.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) >= 1

    def test_setup_logging_invalid_level(self, tmp_path):
        """Test fallback to INFO for invalid log level."""
        # Should not raise, just fallback
        logger = setup_logging(log_level="INVALID_LEVEL")
        assert logger.level == logging.INFO


class TestComputeChecksum:
    @pytest.fixture
    def temp_file(self, tmp_path):
        """Create a temporary file with known content."""
        file_path = tmp_path / "checksum_test.txt"
        content = b"Hello, World! This is a test."
        file_path.write_bytes(content)
        return file_path

    def test_compute_checksum_known_value(self, temp_file):
        """Verify checksum against a known SHA-256 value."""
        # "Hello, World! This is a test." -> SHA256
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" # Placeholder, real calc below
        # Actually calculate real expected for the fixture content
        import hashlib
        real_expected = hashlib.sha256(b"Hello, World! This is a test.").hexdigest()
        
        result = compute_checksum(temp_file)
        assert result == real_expected

    def test_compute_checksum_file_not_found(self):
        """Test that FileNotFoundError is raised for missing files."""
        with pytest.raises(FileNotFoundError):
            compute_checksum("/nonexistent/path/file.txt")

    def test_compute_checksum_invalid_algorithm(self, temp_file):
        """Test that ValueError is raised for invalid algorithms."""
        with pytest.raises(ValueError):
            compute_checksum(temp_file, algorithm="md5_invalid_name")


class TestLogError:
    def test_log_error_basic(self, tmp_path, caplog):
        """Test that log_error captures exception details."""
        log_file = tmp_path / "error_test.log"
        logger = setup_logging(log_level="ERROR", log_file=str(log_file))
        
        test_exception = ValueError("Test error message")
        context = {"key": "value"}
        
        log_error(logger, test_exception, context)
        
        # Check that the log file contains the error message
        content = log_file.read_text()
        assert "ValueError" in content
        assert "Test error message" in content
        assert "key" in content


class TestSafeExit:
    def test_safe_exit_success(self, tmp_path, caplog):
        """Test safe exit with code 0."""
        log_file = tmp_path / "exit_test.log"
        logger = setup_logging(log_level="INFO", log_file=str(log_file))
        
        with patch("sys.exit") as mock_exit:
            safe_exit(logger, code=0, message="Success message")
            mock_exit.assert_called_once_with(0)
        
        content = log_file.read_text()
        assert "Success message" in content
        assert "Exiting with code 0" in content

    def test_safe_exit_failure(self, tmp_path, caplog):
        """Test safe exit with non-zero code."""
        log_file = tmp_path / "exit_test_fail.log"
        logger = setup_logging(log_level="ERROR", log_file=str(log_file))
        
        with patch("sys.exit") as mock_exit:
            safe_exit(logger, code=1, message="Failure message")
            mock_exit.assert_called_once_with(1)
        
        content = log_file.read_text()
        assert "Failure message" in content
        assert "Exiting with code 1" in content