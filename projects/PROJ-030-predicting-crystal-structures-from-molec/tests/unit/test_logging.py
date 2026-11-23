"""
Unit tests for the logging infrastructure (T005).
Verifies that structured JSON logs are produced correctly.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
import logging
from datetime import datetime

import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from logging_config import JSONFormatter, setup_logging, get_logger, log_event


class TestJSONFormatter:
    """Tests for the JSONFormatter class."""

    def test_format_basic_log(self):
        """Test formatting a basic log record."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        output = formatter.format(record)
        log_entry = json.loads(output)

        assert log_entry["level"] == "INFO"
        assert log_entry["logger"] == "test_logger"
        assert log_entry["message"] == "Test message"
        assert "timestamp" in log_entry
        assert log_entry["module"] == "test"
        assert log_entry["line"] == 10

    def test_format_with_exception(self):
        """Test formatting a log record with an exception."""
        formatter = JSONFormatter()
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=20,
            msg="Error occurred",
            args=(),
            exc_info=exc_info
        )
        output = formatter.format(record)
        log_entry = json.loads(output)

        assert log_entry["level"] == "ERROR"
        assert "exception" in log_entry
        assert "ValueError" in log_entry["exception"]

    def test_format_with_extra_fields(self):
        """Test formatting a log record with extra fields."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=30,
            msg="Event occurred",
            args=(),
            exc_info=None
        )
        record.extra_fields = {"event": "test_event", "user_id": 123}
        output = formatter.format(record)
        log_entry = json.loads(output)

        assert log_entry["event"] == "test_event"
        assert log_entry["user_id"] == 123


class TestSetupLogging:
    """Tests for the setup_logging function."""

    def test_creates_log_file(self, tmp_path):
        """Test that setup_logging creates a log file."""
        # Override get_path_logs to use tmp_path
        import logging_config
        original_get_path_logs = logging_config.get_path_logs
        logging_config.get_path_logs = lambda: tmp_path

        try:
            logger = setup_logging(log_file=str(tmp_path / "test.json"), console_output=False)
            assert len(logger.handlers) == 1
            assert isinstance(logger.handlers[0], logging.FileHandler)
        finally:
            logging_config.get_path_logs = original_get_path_logs

    def test_console_output_handler(self, tmp_path):
        """Test that console output handler is added when enabled."""
        import logging_config
        original_get_path_logs = logging_config.get_path_logs
        logging_config.get_path_logs = lambda: tmp_path

        try:
            logger = setup_logging(log_file=str(tmp_path / "test.json"), console_output=True)
            # Should have file handler and console handler
            assert len(logger.handlers) == 2
            handler_types = [type(h).__name__ for h in logger.handlers]
            assert "FileHandler" in handler_types
            assert "StreamHandler" in handler_types
        finally:
            logging_config.get_path_logs = original_get_path_logs

    def test_log_to_default_directory(self, tmp_path):
        """Test logging to the default logs directory."""
        import logging_config
        original_get_path_logs = logging_config.get_path_logs
        logging_config.get_path_logs = lambda: tmp_path

        try:
            logger = setup_logging(console_output=False)
            # Verify a file was created in tmp_path
            files = list(tmp_path.glob("pipeline_*.json"))
            assert len(files) == 1
        finally:
            logging_config.get_path_logs = original_get_path_logs


class TestLogEvent:
    """Tests for the log_event function."""

    def test_log_event_adds_extra_fields(self, tmp_path):
        """Test that log_event correctly adds extra fields to the log."""
        import logging_config
        original_get_path_logs = logging_config.get_path_logs
        logging_config.get_path_logs = lambda: tmp_path

        log_file = tmp_path / "test_event.json"
        try:
            logger = setup_logging(log_file=str(log_file), console_output=False)
            log_event(logger, "test_event", status="success", value=42)

            # Read the log file and verify content
            with open(log_file, 'r') as f:
                line = f.readline()
                log_entry = json.loads(line)

            assert log_entry["event"] == "test_event"
            assert log_entry["status"] == "success"
            assert log_entry["value"] == 42
        finally:
            logging_config.get_path_logs = original_get_path_logs


class TestIntegration:
    """Integration tests for the logging module."""

    def test_full_logging_workflow(self, tmp_path):
        """Test a full logging workflow from setup to reading logs."""
        import logging_config
        original_get_path_logs = logging_config.get_path_logs
        logging_config.get_path_logs = lambda: tmp_path

        log_file = tmp_path / "integration_test.json"
        try:
            # Setup logging
            logger = setup_logging(log_file=str(log_file), console_output=False)

            # Log various events
            logger.info("Starting process")
            log_event(logger, "data_loaded", count=100, source="COD")
            logger.warning("Low memory warning")
            logger.error("An error occurred", exc_info=True)

            # Verify log file exists and contains valid JSON lines
            assert log_file.exists()
            with open(log_file, 'r') as f:
                lines = f.readlines()
                assert len(lines) >= 4  # At least 4 log entries

                for line in lines:
                    entry = json.loads(line)
                    assert "timestamp" in entry
                    assert "level" in entry
                    assert "message" in entry
        finally:
            logging_config.get_path_logs = original_get_path_logs