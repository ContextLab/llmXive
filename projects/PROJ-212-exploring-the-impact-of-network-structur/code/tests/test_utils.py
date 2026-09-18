"""
Unit tests for src/utils.py functionality.

Tests cover:
- Logging setup (file and console handlers)
- Checksum computation (valid files, missing files)
- Error logging with context
- Safe exit behavior
- Timing decorator
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
import hashlib

# Add parent directory to path for imports
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
        """Test logging setup with console output only."""
        logger = setup_logging(log_file=None, console=True, level=logging.DEBUG)
        assert logger.name == "llmXive"
        assert logger.level == logging.DEBUG
        # Should have at least one handler (console)
        assert len(logger.handlers) >= 1
        
        # Verify console handler exists
        console_found = False
        for h in logger.handlers:
            if isinstance(h, logging.StreamHandler) and h.stream == sys.stdout:
                console_found = True
                break
        assert console_found

    def test_setup_logging_with_file(self, tmp_path):
        """Test logging setup with file output."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_file=log_file, console=False)
        
        assert len(logger.handlers) == 1
        file_handler = logger.handlers[0]
        assert isinstance(file_handler, logging.FileHandler)
        assert file_handler.baseFilename == str(log_file)
        
        # Test that logging actually writes to file
        logger.info("Test message")
        # Flush handlers
        for handler in logger.handlers:
            handler.flush()
        
        assert log_file.exists()
        with open(log_file, 'r') as f:
            content = f.read()
        assert "Test message" in content

    def test_setup_logging_duplicate_handlers(self):
        """Test that calling setup_logging multiple times doesn't duplicate handlers."""
        # First call
        logger1 = setup_logging(console=True, log_file=None)
        initial_count = len(logger1.handlers)
        
        # Second call
        logger2 = setup_logging(console=True, log_file=None)
        
        # Should be same logger instance with same handlers
        assert logger1 is logger2
        assert len(logger2.handlers) == initial_count


class TestComputeChecksum:
    def test_compute_checksum_sha256(self, tmp_path):
        """Test checksum computation for a known file."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        checksum = compute_checksum(test_file)
        
        # Verify against known SHA-256
        expected = hashlib.sha256(content).hexdigest()
        assert checksum == expected

    def test_compute_checksum_missing_file(self, tmp_path):
        """Test checksum raises FileNotFoundError for missing file."""
        missing_file = tmp_path / "nonexistent.txt"
        with pytest.raises(FileNotFoundError):
            compute_checksum(missing_file)

    def test_compute_checksum_large_file(self, tmp_path):
        """Test checksum handles large files by reading in chunks."""
        # Create a 1MB file
        large_file = tmp_path / "large.bin"
        chunk = b"x" * 1024
        with open(large_file, 'wb') as f:
            for _ in range(1024):
                f.write(chunk)
        
        checksum = compute_checksum(large_file)
        assert len(checksum) == 64  # SHA-256 hex length
        assert all(c in '0123456789abcdef' for c in checksum)


class TestLogError:
    def test_log_error_basic(self, tmp_path):
        """Test basic error logging."""
        log_file = tmp_path / "error.log"
        logger = setup_logging(log_file=log_file, console=False)
        
        log_error(logger, "Something went wrong")
        
        for handler in logger.handlers:
            handler.flush()
        
        content = log_file.read_text()
        assert "Something went wrong" in content
        assert "ERROR" in content

    def test_log_error_with_exception(self, tmp_path):
        """Test error logging with exception traceback."""
        log_file = tmp_path / "error_exc.log"
        logger = setup_logging(log_file=log_file, console=False)
        
        try:
            raise ValueError("Test exception")
        except Exception as e:
            log_error(logger, "Caught exception", exception=e)
        
        for handler in logger.handlers:
            handler.flush()
        
        content = log_file.read_text()
        assert "Caught exception" in content
        assert "ValueError" in content
        assert "Traceback" in content

    def test_log_error_with_context(self, tmp_path):
        """Test error logging with extra context."""
        log_file = tmp_path / "error_ctx.log"
        logger = setup_logging(log_file=log_file, console=False)
        
        context = {"user_id": 123, "action": "delete"}
        log_error(logger, "Operation failed", extra_context=context)
        
        for handler in logger.handlers:
            handler.flush()
        
        content = log_file.read_text()
        assert "Operation failed" in content
        assert "user_id" in content
        assert "123" in content


class TestSafeExit:
    @patch('sys.exit')
    def test_safe_exit_success(self, mock_exit, tmp_path):
        """Test safe exit with success status."""
        log_file = tmp_path / "exit.log"
        logger = setup_logging(log_file=log_file, console=False)
        
        safe_exit(logger, status=0, message="All done")
        
        mock_exit.assert_called_once_with(0)
        
        for handler in logger.handlers:
            handler.flush()
        
        content = log_file.read_text()
        assert "All done" in content
        assert "successfully" in content

    @patch('sys.exit')
    def test_safe_exit_failure(self, mock_exit, tmp_path):
        """Test safe exit with failure status."""
        log_file = tmp_path / "exit_fail.log"
        logger = setup_logging(log_file=log_file, console=False)
        
        safe_exit(logger, status=1, message="Failed")
        
        mock_exit.assert_called_once_with(1)
        
        for handler in logger.handlers:
            handler.flush()
        
        content = log_file.read_text()
        assert "Failed" in content
        assert "status code 1" in content

    @patch('sys.exit')
    def test_safe_exit_no_logger(self, mock_exit):
        """Test safe exit without logger."""
        safe_exit(status=0)
        mock_exit.assert_called_once_with(0)


class TestTimingDecorator:
    def test_timing_decorator_with_logger(self, tmp_path):
        """Test timing decorator logs execution time."""
        log_file = tmp_path / "timing.log"
        logger = setup_logging(log_file=log_file, console=False)
        
        @timing_decorator(logger)
        def slow_function():
            time.sleep(0.1)
            return 42
        
        result = slow_function()
        assert result == 42
        
        for handler in logger.handlers:
            handler.flush()
        
        content = log_file.read_text()
        assert "slow_function" in content
        assert "seconds" in content

    def test_timing_decorator_without_logger(self, capsys):
        """Test timing decorator prints to console if no logger."""
        @timing_decorator()
        def quick_func():
            time.sleep(0.05)
            return True
        
        result = quick_func()
        assert result is True
        
        captured = capsys.readouterr()
        assert "quick_func" in captured.out
        assert "seconds" in captured.out

    def test_timing_decorator_preserves_function_metadata(self):
        """Test that the decorated function preserves name and docstring."""
        def my_func():
            """My docstring"""
            pass
        
        decorated = timing_decorator()(my_func)
        
        assert decorated.__name__ == "my_func"
        assert decorated.__doc__ == "My docstring"