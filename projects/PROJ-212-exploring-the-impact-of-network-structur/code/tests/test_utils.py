"""
Unit tests for src/utils.py utilities.

Tests cover logging setup, checksum computation, error logging, and safe exit.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import logging
import pytest

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
        """Test logging configuration with console only."""
        logger = setup_logging(log_level="DEBUG", module_name="test_console")
        assert logger.level == logging.DEBUG
        assert len(logger.handlers) >= 1
        # Verify a handler is StreamHandler (console)
        console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(console_handlers) > 0

    def test_setup_logging_with_file(self, tmp_path):
        """Test logging configuration with file output."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_level="INFO", log_file=log_file, module_name="test_file")
        
        assert len(logger.handlers) >= 2  # Console + File
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) > 0
        
        # Verify file exists after writing
        logger.info("Test message")
        assert log_file.exists()

    def test_setup_logging_duplicate_handlers(self):
        """Test that calling setup_logging twice doesn't duplicate handlers."""
        logger = setup_logging(module_name="test_dup")
        initial_count = len(logger.handlers)
        
        # Call again
        logger_again = setup_logging(module_name="test_dup")
        
        assert len(logger_again.handlers) == initial_count


class TestComputeChecksum:
    def test_checksum_string(self):
        """Test checksum of a string."""
        data = "test data"
        checksum = compute_checksum(data)
        assert len(checksum) == 64  # SHA256 hex length
        assert isinstance(checksum, str)

    def test_checksum_bytes(self):
        """Test checksum of bytes."""
        data = b"test data"
        checksum = compute_checksum(data)
        assert len(checksum) == 64

    def test_checksum_dict_deterministic(self):
        """Test that dictionary checksum is deterministic regardless of key order."""
        data1 = {"b": 2, "a": 1}
        data2 = {"a": 1, "b": 2}
        
        checksum1 = compute_checksum(data1)
        checksum2 = compute_checksum(data2)
        
        assert checksum1 == checksum2

    def test_checksum_invalid_algorithm(self):
        """Test that unsupported algorithm raises ValueError."""
        with pytest.raises(ValueError):
            compute_checksum("data", algorithm="invalid_algo")

    def test_checksum_unserializable_object(self):
        """Test that unserializable objects raise ValueError."""
        class Unserializable:
            pass
        
        with pytest.raises(ValueError):
            compute_checksum(Unserializable())


class TestLogError:
    def test_log_error_basic(self, caplog):
        """Test basic error logging."""
        logger = logging.getLogger("test_error_basic")
        logger.setLevel(logging.DEBUG)
        
        with caplog.at_level(logging.ERROR):
            log_error(logger, "Something went wrong")
        
        assert "Something went wrong" in caplog.text

    def test_log_error_with_exception(self, caplog):
        """Test error logging with exception details."""
        logger = logging.getLogger("test_error_exc")
        logger.setLevel(logging.DEBUG)
        
        exc = ValueError("Test error")
        
        with caplog.at_level(logging.ERROR):
            log_error(logger, "Failed", error=exc)
        
        assert "Failed" in caplog.text
        assert "ValueError" in caplog.text
        assert "Test error" in caplog.text

    def test_log_error_with_context(self, caplog):
        """Test error logging with context."""
        logger = logging.getLogger("test_error_ctx")
        logger.setLevel(logging.DEBUG)
        
        with caplog.at_level(logging.ERROR):
            log_error(logger, "Failed", context={"user_id": 123, "action": "login"})
        
        assert "Failed" in caplog.text
        assert "user_id=123" in caplog.text
        assert "action=login" in caplog.text


class TestSafeExit:
    @patch('sys.exit')
    def test_safe_exit_success(self, mock_exit, caplog):
        """Test safe exit on success."""
        logger = logging.getLogger("test_exit_success")
        logger.setLevel(logging.INFO)
        
        with caplog.at_level(logging.INFO):
            safe_exit(logger, exit_code=0, message="All good")
        
        assert "SUCCESS" in caplog.text
        assert "All good" in caplog.text
        mock_exit.assert_called_once_with(0)

    @patch('sys.exit')
    def test_safe_exit_failure(self, mock_exit, caplog):
        """Test safe exit on failure."""
        logger = logging.getLogger("test_exit_fail")
        logger.setLevel(logging.CRITICAL)
        
        exc = RuntimeError("Critical failure")
        
        with caplog.at_level(logging.CRITICAL):
            safe_exit(logger, exit_code=1, message="Crashed", error=exc)
        
        assert "CRITICAL" in caplog.text
        assert "Crashed" in caplog.text
        assert "RuntimeError" in caplog.text
        mock_exit.assert_called_once_with(1)


class TestTimingDecorator:
    def test_timing_decorator_success(self, caplog):
        """Test timing decorator on successful function."""
        logger = logging.getLogger("test_timing")
        logger.setLevel(logging.INFO)
        
        @timing_decorator(logger=logger, log_level="INFO")
        def slow_function():
            import time
            time.sleep(0.1)
            return "done"
        
        with caplog.at_level(logging.INFO):
            result = slow_function()
        
        assert result == "done"
        assert "completed in" in caplog.text
        assert "0.1" in caplog.text  # Should show approx 0.1s

    def test_timing_decorator_failure(self, caplog):
        """Test timing decorator on failing function."""
        logger = logging.getLogger("test_timing_fail")
        logger.setLevel(logging.ERROR)
        
        @timing_decorator(logger=logger, log_level="ERROR")
        def failing_function():
            raise ValueError("Boom")
        
        with pytest.raises(ValueError):
            with caplog.at_level(logging.ERROR):
                failing_function()
        
        assert "failed after" in caplog.text
        assert "ValueError" in caplog.text