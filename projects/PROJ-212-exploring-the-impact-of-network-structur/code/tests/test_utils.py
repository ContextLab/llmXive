"""
Unit tests for src/utils.py utility functions.
"""
import os
import sys
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import logging

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import (
    setup_logging,
    compute_checksum,
    log_error,
    safe_exit,
    timing_decorator
)


class TestSetupLogging:
    def test_setup_logging_console_only(self, tmp_path):
        """Test logging setup with console only (no file)."""
        logger = setup_logging(log_file=None, level=logging.DEBUG)
        assert logger.level == logging.DEBUG
        # Should have at least one handler (console)
        assert len(logger.handlers) >= 1

    def test_setup_logging_with_file(self, tmp_path):
        """Test logging setup with file and console handlers."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_file=log_file, level=logging.INFO)

        assert logger.level == logging.INFO
        # Should have at least 2 handlers (console + file)
        assert len(logger.handlers) >= 2

        # Verify file was created
        assert log_file.exists()

    def test_setup_logging_creates_directories(self, tmp_path):
        """Test that setup_logging creates parent directories for log file."""
        nested_log = tmp_path / "nested" / "dir" / "test.log"
        logger = setup_logging(log_file=nested_log)
        assert nested_log.exists()


class TestComputeChecksum:
    def test_compute_checksum_valid_file(self, tmp_path):
        """Test checksum computation on a valid file."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)

        checksum = compute_checksum(test_file)
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA-256 hex length

    def test_compute_checksum_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        missing_file = tmp_path / "nonexistent.txt"
        with pytest.raises(FileNotFoundError):
            compute_checksum(missing_file)

    def test_compute_checksum_invalid_algorithm(self, tmp_path):
        """Test that ValueError is raised for unsupported algorithm."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"test")

        with pytest.raises(ValueError):
            compute_checksum(test_file, algorithm="invalid_algo")

    def test_compute_checksum_large_file(self, tmp_path):
        """Test checksum computation on a large file (chunked reading)."""
        large_file = tmp_path / "large.bin"
        # Create a 1MB file
        large_file.write_bytes(b"x" * (1024 * 1024))

        checksum = compute_checksum(large_file)
        assert isinstance(checksum, str)
        assert len(checksum) == 64


class TestLogError:
    def test_log_error_basic(self, tmp_path):
        """Test basic error logging."""
        log_file = tmp_path / "error.log"
        logger = setup_logging(log_file=log_file, level=logging.ERROR)

        test_error = ValueError("Test error message")
        log_error(logger, test_error)

        assert log_file.exists()
        content = log_file.read_text()
        assert "Test error message" in content
        assert "ValueError" in content

    def test_log_error_with_context(self, tmp_path):
        """Test error logging with context dictionary."""
        log_file = tmp_path / "error_context.log"
        logger = setup_logging(log_file=log_file, level=logging.ERROR)

        test_error = RuntimeError("Context error")
        context = {"input_id": 123, "status": "failed"}
        log_error(logger, test_error, context=context)

        content = log_file.read_text()
        assert "Context error" in content
        assert "123" in content
        assert "failed" in content


class TestSafeExit:
    def test_safe_exit_success(self, tmp_path):
        """Test safe exit with success status."""
        log_file = tmp_path / "exit.log"
        logger = setup_logging(log_file=log_file, level=logging.INFO)

        # Mock sys.exit to prevent actual exit
        with patch('sys.exit') as mock_exit:
            safe_exit(logger, status=0, message="Success message")
            mock_exit.assert_called_once_with(0)

        content = log_file.read_text()
        assert "Success message" in content or "completed successfully" in content.lower()

    def test_safe_exit_failure(self, tmp_path):
        """Test safe exit with failure status."""
        log_file = tmp_path / "exit_fail.log"
        logger = setup_logging(log_file=log_file, level=logging.ERROR)

        with patch('sys.exit') as mock_exit:
            safe_exit(logger, status=1, message="Failure message")
            mock_exit.assert_called_once_with(1)

        content = log_file.read_text()
        assert "Failure message" in content or "exited with status code 1" in content.lower()


class TestTimingDecorator:
    def test_timing_decorator_success(self, tmp_path):
        """Test that timing_decorator measures execution time."""
        log_file = tmp_path / "timing.log"
        setup_logging(log_file=log_file, level=logging.INFO)

        @timing_decorator
        def slow_function():
            time.sleep(0.1)
            return "done"

        result = slow_function()
        assert result == "done"

        content = log_file.read_text()
        assert "completed in" in content.lower()
        assert "seconds" in content.lower()

    def test_timing_decorator_with_exception(self, tmp_path):
        """Test that timing_decorator logs time even if function raises."""
        log_file = tmp_path / "timing_exc.log"
        setup_logging(log_file=log_file, level=logging.INFO)

        @timing_decorator
        def failing_function():
            time.sleep(0.05)
            raise ValueError("Intentional error")

        with pytest.raises(ValueError):
            failing_function()

        # Should still log timing
        content = log_file.read_text()
        assert "completed in" in content.lower()