"""
Unit tests for the logging utilities.
"""
import json
import logging
import tempfile
from pathlib import Path

import pytest

from src.utils.logging import (
    JsonFormatter,
    get_logger,
    log_event,
    setup_logging,
)


class TestJsonFormatter:
    def test_format_produces_valid_json(self):
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        assert json.loads(output) is not None

    def test_format_includes_required_fields(self):
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        log_data = json.loads(output)

        assert "timestamp" in log_data
        assert "level" in log_data
        assert "logger" in log_data
        assert "message" in log_data
        assert "module" in log_data
        assert "line" in log_data


class TestSetupLogging:
    def test_setup_logging_creates_handlers(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            logger = setup_logging(level=logging.INFO, log_file=str(log_file))

            assert len(logger.handlers) >= 1

            # Clean up
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)

    def test_setup_logging_with_console_only(self):
        logger = setup_logging(level=logging.INFO, include_console=True, log_file=None)
        assert len(logger.handlers) >= 1

        # Clean up
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)


class TestGetLogger:
    def test_get_logger_returns_logger(self):
        logger = get_logger("test.module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"


class TestLogEvent:
    def test_log_event_with_extra_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test_event.log"
            setup_logging(level=logging.INFO, log_file=str(log_file), include_console=False)
            logger = get_logger("test.event")

            log_event(logger, "INFO", "Test event", user_id=123, action="test")

            with open(log_file, "r") as f:
                line = f.readline()
                log_data = json.loads(line)

            assert log_data["message"] == "Test event"
            assert log_data["data"]["user_id"] == 123
            assert log_data["data"]["action"] == "test"

            # Clean up
            logging.getLogger().handlers.clear()
