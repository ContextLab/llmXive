"""
Tests for the structured logging module.
"""
import json
import logging
import sys
import tempfile
from pathlib import Path
from io import StringIO

import pytest

from code.utils.logging import (
    setup_logging,
    get_logger,
    log_info,
    log_warning,
    log_error,
    log_debug,
    log_critical,
    log_event,
    StructuredFormatter,
)


class TestStructuredFormatter:
    """Tests for the JSON log formatter."""

    def test_format_basic_message(self):
        """Test formatting a basic log message."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        log_data = json.loads(output)

        assert log_data["level"] == "INFO"
        assert log_data["message"] == "Test message"
        assert "timestamp" in log_data
        assert log_data["logger"] == "test"

    def test_format_with_extra_fields(self):
        """Test formatting with extra context fields."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.task_id = "T001"
        record.run_id = "run_123"
        record.dataset_id = "dataset_A"
        record.extra_data = {"key": "value"}

        output = formatter.format(record)
        log_data = json.loads(output)

        assert log_data["task_id"] == "T001"
        assert log_data["run_id"] == "run_123"
        assert log_data["dataset_id"] == "dataset_A"
        assert log_data["extra"] == {"key": "value"}

    def test_format_with_exception(self):
        """Test formatting with exception info."""
        formatter = StructuredFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=1,
                msg="Error occurred",
                args=(),
                exc_info=exc_info,
            )

        output = formatter.format(record)
        log_data = json.loads(output)

        assert log_data["level"] == "ERROR"
        assert "exception" in log_data
        assert "ValueError" in log_data["exception"]


class TestLoggingSetup:
    """Tests for logging initialization."""

    def test_setup_logging_console_only(self, capsys):
        """Test setup with console output only."""
        logger = setup_logging(
            log_level="INFO",
            log_file=None,
            enable_console=True,
            task_id="T001",
        )

        assert logger is not None
        assert len(logger.handlers) == 1

        logger.info("Test message")
        captured = capsys.readouterr()
        log_data = json.loads(captured.out.strip())

        assert log_data["message"] == "Test message"
        assert log_data["task_id"] == "T001"

    def test_setup_logging_with_file(self, tmp_path):
        """Test setup with file output."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(
            log_level="INFO",
            log_file=log_file,
            enable_console=False,
        )

        assert len(logger.handlers) == 1

        logger.info("Test file message")

        assert log_file.exists()
        with open(log_file, "r") as f:
            content = f.read()
            log_data = json.loads(content.strip())

        assert log_data["message"] == "Test file message"

    def test_setup_logging_creates_directory(self, tmp_path):
        """Test that setup creates parent directories for log file."""
        nested_log_file = tmp_path / "subdir" / "nested" / "test.log"
        logger = setup_logging(
            log_level="INFO",
            log_file=nested_log_file,
            enable_console=False,
        )

        assert nested_log_file.parent.exists()
        assert nested_log_file.parent.is_dir()


class TestLogFunctions:
    """Tests for convenience logging functions."""

    def test_log_info(self, capsys):
        """Test log_info function."""
        setup_logging(enable_console=True, log_file=None)
        log_info("Info message", task_id="T002")

        captured = capsys.readouterr()
        log_data = json.loads(captured.out.strip())

        assert log_data["level"] == "INFO"
        assert log_data["message"] == "Info message"

    def test_log_warning(self, capsys):
        """Test log_warning function."""
        setup_logging(enable_console=True, log_file=None)
        log_warning("Warning message", task_id="T003")

        captured = capsys.readouterr()
        log_data = json.loads(captured.out.strip())

        assert log_data["level"] == "WARNING"

    def test_log_error(self, capsys):
        """Test log_error function."""
        setup_logging(enable_console=True, log_file=None)
        log_error("Error message", task_id="T004")

        captured = capsys.readouterr()
        log_data = json.loads(captured.out.strip())

        assert log_data["level"] == "ERROR"

    def test_log_debug(self, capsys):
        """Test log_debug function (requires DEBUG level)."""
        setup_logging(log_level="DEBUG", enable_console=True, log_file=None)
        log_debug("Debug message", task_id="T005")

        captured = capsys.readouterr()
        log_data = json.loads(captured.out.strip())

        assert log_data["level"] == "DEBUG"

    def test_log_critical(self, capsys):
        """Test log_critical function."""
        setup_logging(enable_console=True, log_file=None)
        log_critical("Critical message", task_id="T006")

        captured = capsys.readouterr()
        log_data = json.loads(captured.out.strip())

        assert log_data["level"] == "CRITICAL"

    def test_log_event_with_extra_data(self, capsys):
        """Test log_event with extra context."""
        setup_logging(enable_console=True, log_file=None)
        log_event(
            "INFO",
            "Event with extra",
            task_id="T007",
            run_id="run_456",
            dataset_id="dataset_B",
            extra_data={"metric": 0.95, "samples": 100},
        )

        captured = capsys.readouterr()
        log_data = json.loads(captured.out.strip())

        assert log_data["task_id"] == "T007"
        assert log_data["run_id"] == "run_456"
        assert log_data["dataset_id"] == "dataset_B"
        assert log_data["extra"] == {"metric": 0.95, "samples": 100}

    def test_get_logger_returns_singleton(self):
        """Test that get_logger returns the same instance."""
        setup_logging(task_id="T008")
        logger1 = get_logger()
        logger2 = get_logger()

        assert logger1 is logger2

    def test_get_logger_initializes_if_not_set(self):
        """Test that get_logger initializes logger if not set."""
        # Reset global state (simulating fresh start)
        import code.utils.logging as logging_module
        logging_module._logger = None
        logging_module._handler = None

        logger = get_logger()

        assert logger is not None
        assert len(logger.handlers) > 0
