import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import logging

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.logging import (
    JsonFormatter,
    setup_logger,
    get_logger,
    log_error,
    log_warning,
    log_info,
    log_debug,
    log_success,
)


class TestJsonFormatter:
    def test_format_returns_json_string(self):
        formatter = JsonFormatter()
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
        assert isinstance(output, str)
        data = json.loads(output)
        assert "timestamp" in data
        assert data["level"] == "INFO"
        assert data["message"] == "Test message"

    def test_format_includes_exception(self):
        formatter = JsonFormatter()
        try:
            raise ValueError("Test error")
        except Exception:
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=1,
                msg="Error occurred",
                args=(),
                exc_info=sys.exc_info(),
            )
            output = formatter.format(record)
            data = json.loads(output)
            assert "exception" in data
            assert data["exception"]["type"] == "ValueError"


class TestSetupLogger:
    def test_setup_logger_returns_logger(self):
        logger = setup_logger(name="test_setup", console=False)
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_setup"

    def test_setup_logger_creates_file_handler(self, tmp_path):
        log_file = tmp_path / "test.log"
        logger = setup_logger(
            name="test_file", log_file=str(log_file), console=False
        )
        assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)

    def test_setup_logger_creates_console_handler(self):
        logger = setup_logger(name="test_console", console=True)
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)


class TestGetLogger:
    def test_get_logger_returns_existing(self):
        name = "test_get_existing"
        setup_logger(name=name, console=False)
        logger1 = get_logger(name)
        logger2 = get_logger(name)
        assert logger1 is logger2

    def test_get_logger_initializes_if_missing(self):
        name = "test_get_new"
        # Ensure no handlers exist
        logger = logging.getLogger(name)
        logger.handlers = []
        retrieved = get_logger(name)
        assert len(retrieved.handlers) > 0


class TestLogFunctions:
    @pytest.fixture(autouse=True)
    def cleanup_loggers(self):
        # Cleanup to prevent cross-test interference
        yield
        for name in ["elastic_anisotropy", "test_error", "test_warning", "test_info", "test_debug", "test_success"]:
            logger = logging.getLogger(name)
            logger.handlers = []

    def test_log_error(self, caplog):
        with caplog.at_level(logging.ERROR):
            log_error("Test error", logger_name="test_error")
        assert any("Test error" in record.message for record in caplog.records)
        assert any(record.levelname == "ERROR" for record in caplog.records)

    def test_log_warning(self, caplog):
        with caplog.at_level(logging.WARNING):
            log_warning("Test warning", logger_name="test_warning")
        assert any("Test warning" in record.message for record in caplog.records)
        assert any(record.levelname == "WARNING" for record in caplog.records)

    def test_log_info(self, caplog):
        with caplog.at_level(logging.INFO):
            log_info("Test info", logger_name="test_info")
        assert any("Test info" in record.message for record in caplog.records)
        assert any(record.levelname == "INFO" for record in caplog.records)

    def test_log_debug(self, caplog):
        with caplog.at_level(logging.DEBUG):
            log_debug("Test debug", logger_name="test_debug")
        assert any("Test debug" in record.message for record in caplog.records)
        assert any(record.levelname == "DEBUG" for record in caplog.records)

    def test_log_success(self, caplog):
        with caplog.at_level(logging.INFO):
            log_success("Test success", logger_name="test_success")
        assert any("Test success" in record.message for record in caplog.records)
        assert any(record.levelname == "INFO" for record in caplog.records)