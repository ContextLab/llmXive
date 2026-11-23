"""
Unit tests for the logging infrastructure (src/utils/logger.py).
"""

import json
import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Import the module to test
import src.utils.logger as logger_module


class TestStructuredFormatter:
    """Tests for the StructuredFormatter class."""

    def test_format_includes_required_fields(self):
        """Verify that formatted log messages contain timestamp, level, and message."""
        formatter = logger_module.StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)
        log_data = json.loads(formatted)

        assert "timestamp" in log_data
        assert log_data["level"] == "INFO"
        assert log_data["message"] == "Test message"
        assert log_data["module"] == "test"

    def test_format_includes_exception_info(self):
        """Verify that exceptions are included in the JSON output."""
        formatter = logger_module.StructuredFormatter()
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=1,
                msg="An error occurred",
                args=(),
                exc_info=sys.exc_info(),
            )

            formatted = formatter.format(record)
            log_data = json.loads(formatted)

            assert "exception" in log_data
            assert "ValueError" in log_data["exception"]
            assert "Test error" in log_data["exception"]

    def test_format_includes_extra_data(self):
        """Verify that extra data is merged into the JSON output."""
        formatter = logger_module.StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.extra_data = {"event_type": "test_event", "user_id": 123}

        formatted = formatter.format(record)
        log_data = json.loads(formatted)

        assert log_data["event_type"] == "test_event"
        assert log_data["user_id"] == 123


class TestLogEvent:
    """Tests for the log_event function."""

    def test_log_event_creates_json_entry(self):
        """Verify that log_event writes a valid JSON entry to the file handler."""
        # Temporarily redirect log file to a temp location
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test_run.log")
            with patch.object(logger_module, "ARTIFACTS_DIR", tmpdir), \
                 patch.object(logger_module, "LOG_FILE_PATH", log_path), \
                 patch.object(logger_module, "_initialized", False):
                
                # Re-initialize logger to use temp path
                logger_module._setup_logging()
                
                logger_module.log_event(
                    "test_event", 
                    "Test message", 
                    extra_field="value"
                )
                
                # Verify file exists and contains JSON
                assert os.path.exists(log_path)
                with open(log_path, "r") as f:
                    line = f.readline()
                    log_data = json.loads(line)
                    
                    assert log_data["message"] == "Test message"
                    assert log_data["event_type"] == "test_event"
                    assert log_data["extra_field"] == "value"


class TestLogError:
    """Tests for the log_error function."""

    def test_log_error_with_exception(self):
        """Verify that log_error includes exception traceback."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test_run.log")
            with patch.object(logger_module, "ARTIFACTS_DIR", tmpdir), \
                 patch.object(logger_module, "LOG_FILE_PATH", log_path), \
                 patch.object(logger_module, "_initialized", False):
                
                logger_module._setup_logging()
                
                try:
                    raise RuntimeError("Critical failure")
                except RuntimeError as e:
                    logger_module.log_error("System crashed", exception=e)
                
                with open(log_path, "r") as f:
                    line = f.readline()
                    log_data = json.loads(line)
                    
                    assert log_data["message"] == "System crashed"
                    assert "exception" in log_data
                    assert "RuntimeError" in log_data["exception"]

    def test_log_error_with_context(self):
        """Verify that log_error includes context data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test_run.log")
            with patch.object(logger_module, "ARTIFACTS_DIR", tmpdir), \
                 patch.object(logger_module, "LOG_FILE_PATH", log_path), \
                 patch.object(logger_module, "_initialized", False):
                
                logger_module._setup_logging()
                
                context = {"dataset": "Auto", "rows": 100}
                logger_module.log_error("Data error", context=context)
                
                with open(log_path, "r") as f:
                    line = f.readline()
                    log_data = json.loads(line)
                    
                    assert log_data["context"]["dataset"] == "Auto"
                    assert log_data["context"]["rows"] == 100