"""
Unit tests for the structured logging module (T008).
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
from src.utils.logging import (
    JsonFormatter,
    PipelineLogger,
    get_logger,
    log_event,
    log_error,
    log_progress,
)


class TestJsonFormatter:
    """Tests for the JSON log formatter."""

    def test_format_includes_timestamp(self):
        """Verify timestamp is included in JSON output."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        output = formatter.format(record)
        log_data = json.loads(output)
        assert "timestamp" in log_data
        assert "level" in log_data
        assert log_data["level"] == "INFO"
        assert log_data["message"] == "Test message"

    def test_format_includes_exception(self):
        """Verify exception info is included when present."""
        formatter = JsonFormatter()
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=15,
            msg="Error occurred",
            args=(),
            exc_info=exc_info
        )
        output = formatter.format(record)
        log_data = json.loads(output)
        assert "exception" in log_data
        assert "ValueError" in log_data["exception"]

    def test_format_includes_extra_fields(self):
        """Verify extra fields are included in output."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=20,
            msg="Test with extra",
            args=(),
            exc_info=None
        )
        record.extra_fields = {"task_id": "T008", "status": "running"}
        output = formatter.format(record)
        log_data = json.loads(output)
        assert log_data["task_id"] == "T008"
        assert log_data["status"] == "running"


class TestPipelineLogger:
    """Tests for the PipelineLogger class."""

    def test_logger_creates_file(self):
        """Verify logger creates log file when path provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = PipelineLogger("test_logger", log_file=log_path)
            logger.log_event("TEST", "Test message")
            assert log_path.exists()

    def test_logger_writes_json(self):
        """Verify log file contains valid JSON lines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = PipelineLogger("test_logger", log_file=log_path)
            logger.log_event("TEST", "Test message", key="value")
            with open(log_path, 'r') as f:
                line = f.readline()
                log_data = json.loads(line)
                assert log_data["message"] == "Test message"
                assert log_data["key"] == "value"

    def test_log_event_includes_type(self):
        """Verify event_type is included in log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = PipelineLogger("test_logger", log_file=log_path)
            logger.log_event("START", "Starting process")
            with open(log_path, 'r') as f:
                line = f.readline()
                log_data = json.loads(line)
                assert log_data["event_type"] == "START"

    def test_log_error_includes_exception(self):
        """Verify error logs include exception details."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = PipelineLogger("test_logger", log_file=log_path)
            try:
                raise RuntimeError("Test failure")
            except RuntimeError as e:
                logger.log_error("Operation failed", error=e)
            with open(log_path, 'r') as f:
                line = f.readline()
                log_data = json.loads(line)
                assert "exception" in log_data
                assert "RuntimeError" in log_data["exception"]

    def test_log_progress_includes_percent(self):
        """Verify progress logs include percentage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            logger = PipelineLogger("test_logger", log_file=log_path)
            logger.log_progress(5, 10, "Processing")
            with open(log_path, 'r') as f:
                line = f.readline()
                log_data = json.loads(line)
                assert log_data["current"] == 5
                assert log_data["total"] == 10
                assert log_data["percent"] == 50.0


class TestConvenienceFunctions:
    """Tests for convenience logging functions."""

    def test_log_event_function(self):
        """Test global log_event function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            # Override default logger file
            import src.utils.logging as logging_module
            original_logger = logging_module.get_logger()
            logging_module._thread_local.loggers = {
                "pipeline": PipelineLogger("pipeline", log_file=log_path)
            }
            log_event("Test global event", event_type="GLOBAL", extra="data")
            with open(log_path, 'r') as f:
                line = f.readline()
                log_data = json.loads(line)
                assert log_data["event_type"] == "GLOBAL"

    def test_log_error_function(self):
        """Test global log_error function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            import src.utils.logging as logging_module
            logging_module._thread_local.loggers = {
                "pipeline": PipelineLogger("pipeline", log_file=log_path)
            }
            try:
                raise ValueError("Test")
            except ValueError as e:
                log_error("Global error", error=e)
            with open(log_path, 'r') as f:
                line = f.readline()
                log_data = json.loads(line)
                assert "exception" in log_data

    def test_log_progress_function(self):
        """Test global log_progress function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test.log"
            import src.utils.logging as logging_module
            logging_module._thread_local.loggers = {
                "pipeline": PipelineLogger("pipeline", log_file=log_path)
            }
            log_progress(100, 200, "Final Stage")
            with open(log_path, 'r') as f:
                line = f.readline()
                log_data = json.loads(line)
                assert log_data["percent"] == 50.0
                assert log_data["stage"] == "Final Stage"