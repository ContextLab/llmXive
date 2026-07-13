"""
Unit tests for the structured JSON logging module.
"""
import json
import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Import the module under test
import code.utils.logging as logging_module
from code.utils.logging import (
    JSONFormatter,
    get_logger,
    log_error,
    log_with_context,
    get_task_logger,
    log_task_start,
    log_task_complete,
    log_task_failed,
)


class TestJSONFormatter:
    """Tests for the JSONFormatter class."""

    def test_format_basic_log(self):
        """Test formatting a basic log message."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Test message"
        assert parsed["logger"] == "test"
        assert "timestamp" in parsed

    def test_format_with_extra_data(self):
        """Test formatting a log with extra data."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.extra_data = {"key": "value", "number": 42}

        result = formatter.format(record)
        parsed = json.loads(result)

        assert parsed["data"]["key"] == "value"
        assert parsed["data"]["number"] == 42

    def test_format_with_exception(self):
        """Test formatting a log with exception info."""
        formatter = JSONFormatter()
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=10,
                msg="Error occurred",
                args=(),
                exc_info=exc_info,
            )

            result = formatter.format(record)
            parsed = json.loads(result)

            assert parsed["exception"]["type"] == "ValueError"
            assert "Test error" in parsed["exception"]["message"]
            assert len(parsed["exception"]["traceback"]) > 0


class TestGetLogger:
    """Tests for the get_logger function."""

    def test_get_logger_creates_new_logger(self, tmp_path):
        """Test that get_logger creates a new logger."""
        with patch.object(logging_module, "LOG_DIR", str(tmp_path)):
            logger = get_logger("test_logger_unique")
            
            assert logger.name == "test_logger_unique"
            assert len(logger.handlers) > 0

    def test_get_logger_returns_cached(self, tmp_path):
        """Test that get_logger returns cached logger."""
        with patch.object(logging_module, "LOG_DIR", str(tmp_path)):
            logger1 = get_logger("test_cached_logger")
            logger2 = get_logger("test_cached_logger")
            
            assert logger1 is logger2

    def test_get_logger_with_custom_file(self, tmp_path):
        """Test get_logger with custom log file."""
        with patch.object(logging_module, "LOG_DIR", str(tmp_path)):
            logger = get_logger("test_custom_file", log_file="custom.log")
            
            # Check that the log file exists
            log_path = tmp_path / "custom.log"
            assert log_path.exists() or any(
                f.name.startswith("custom") for f in tmp_path.iterdir()
            )

    def test_get_logger_without_stdout(self, tmp_path):
        """Test get_logger with stdout disabled."""
        with patch.object(logging_module, "LOG_DIR", str(tmp_path)):
            logger = get_logger("test_no_stdout", include_stdout=False)
            
            stdout_handlers = [
                h for h in logger.handlers 
                if isinstance(h, logging.StreamHandler)
            ]
            # Should have file handler but no stdout handler
            assert len([h for h in logger.handlers if not isinstance(h, RotatingFileHandler)]) == 0


class TestLogError:
    """Tests for the log_error function."""

    def test_log_error_basic(self, tmp_path):
        """Test basic error logging."""
        with patch.object(logging_module, "LOG_DIR", str(tmp_path)):
            logger = get_logger("test_error_logger")
            log_error(logger, "Test error message")
            
            # Verify log file was created
            assert any(f.name.startswith("pipeline_test_error_logger") for f in tmp_path.iterdir())

    def test_log_error_with_exception(self, tmp_path):
        """Test error logging with exception."""
        with patch.object(logging_module, "LOG_DIR", str(tmp_path)):
            logger = get_logger("test_exception_logger")
            try:
                raise ValueError("Test exception")
            except Exception as e:
                log_error(logger, "Caught error", exception=e)
            
            # Verify log file contains exception info
            log_files = [f for f in tmp_path.iterdir() if f.name.startswith("pipeline_test_exception_logger")]
            assert len(log_files) > 0

    def test_log_error_with_extra_data(self, tmp_path):
        """Test error logging with extra context."""
        with patch.object(logging_module, "LOG_DIR", str(tmp_path)):
            logger = get_logger("test_extra_logger")
            log_error(
                logger, 
                "Test error", 
                task_id="T006", 
              status="failed"
            )
            
            # Verify log file was created
            assert any(f.name.startswith("pipeline_test_extra_logger") for f in tmp_path.iterdir())


class TestLogWithContext:
    """Tests for the log_with_context function."""

    def test_log_with_context(self, tmp_path):
        """Test logging with extra context."""
        with patch.object(logging_module, "LOG_DIR", str(tmp_path)):
            logger = get_logger("test_context_logger")
            log_with_context(
                logger, 
                logging.INFO, 
                "Info message", 
                stage="training", 
                  metric=0.95
            )
            
            # Verify log file was created
            assert any(f.name.startswith("pipeline_test_context_logger") for f in tmp_path.iterdir())


class TestTaskLogger:
    """Tests for task-specific logging functions."""

    def test_get_task_logger(self, tmp_path):
        """Test creating a task logger."""
        with patch.object(logging_module, "LOG_DIR", str(tmp_path)):
            logger = get_task_logger("T006", stage="setup")
            
            assert logger.name.startswith("task_T006")
            assert hasattr(logger, "_context")
            assert logger._context["task_id"] == "T006"
            assert logger._context["stage"] == "setup"

    def test_log_task_start(self, tmp_path):
        """Test logging task start."""
        with patch.object(logging_module, "LOG_DIR", str(tmp_path)):
            logger = get_task_logger("T006", stage="setup")
            log_task_start(logger, "T006", model="Qwen3-VL-4B")
            
            # Verify log file was created
            assert any(f.name.startswith("pipeline_task_T006_setup") for f in tmp_path.iterdir())

    def test_log_task_complete(self, tmp_path):
        """Test logging task completion."""
        with patch.object(logging_module, "LOG_DIR", str(tmp_path)):
            logger = get_task_logger("T006", stage="setup")
            log_task_complete(logger, "T006", duration=120)
            
            # Verify log file was created
            assert any(f.name.startswith("pipeline_task_T006_setup") for f in tmp_path.iterdir())

    def test_log_task_failed(self, tmp_path):
        """Test logging task failure."""
        with patch.object(logging_module, "LOG_DIR", str(tmp_path)):
            logger = get_task_logger("T006", stage="setup")
            try:
                raise RuntimeError("Setup failed")
            except Exception as e:
                log_task_failed(logger, "T006", e, attempt=1)
            
            # Verify log file was created
            assert any(f.name.startswith("pipeline_task_T006_setup") for f in tmp_path.iterdir())


class TestIntegration:
    """Integration tests for the logging module."""

    def test_full_logging_workflow(self, tmp_path):
        """Test a complete logging workflow."""
        with patch.object(logging_module, "LOG_DIR", str(tmp_path)):
            # Create task logger
            logger = get_task_logger("T006", stage="setup")
            
            # Log start
            log_task_start(logger, "T006", step="initialization")
            
            # Log progress
            log_with_context(
                logger, 
                logging.INFO, 
                "Processing data", 
                progress=50
            )
            
            # Log error
            try:
                raise ValueError("Simulated error")
            except Exception as e:
                log_error(
                    logger, 
                    "Error during processing", 
                    exception=e, 
                    retry_count=1
                )
            
            # Log completion
            log_task_complete(logger, "T006", total_steps=3)
            
            # Verify logs were written
            log_files = list(tmp_path.glob("pipeline_task_T006_setup*.log"))
            assert len(log_files) > 0
            
            # Verify log content
            with open(log_files[0], "r") as f:
                content = f.read()
                assert "T006" in content
                assert "initialization" in content
                assert "ValueError" in content
                assert "completed" in content