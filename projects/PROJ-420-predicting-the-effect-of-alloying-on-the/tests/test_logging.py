"""Tests for the logging infrastructure."""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from logging_config import (
    LogEntry,
    JSONFormatter,
    ReproducibilityLogger,
    setup_logging,
    get_logger,
    log_operation,
    log_with_extra,
)


class TestLogEntry:
    """Tests for LogEntry dataclass."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        entry = LogEntry()
        assert entry.timestamp is not None
        assert entry.level == "INFO"
        assert entry.message == ""
        assert entry.trace_id is not None
        assert entry.module == "root"
        assert entry.operation is None
        assert entry.parameters == {}
        assert entry.success is None
        assert entry.duration_ms is None
        assert entry.error is None

    def test_custom_values(self):
        """Test setting custom values."""
        entry = LogEntry(
            level="ERROR",
            message="Test error",
            module="test_module",
            operation="test_op",
            parameters={"key": "value"},
            success=False,
            duration_ms=100.5,
            error="Something went wrong"
        )
        assert entry.level == "ERROR"
        assert entry.message == "Test error"
        assert entry.module == "test_module"
        assert entry.operation == "test_op"
        assert entry.parameters == {"key": "value"}
        assert entry.success is False
        assert entry.duration_ms == 100.5
        assert entry.error == "Something went wrong"

    def test_to_json(self):
        """Test JSON serialization."""
        entry = LogEntry(
            level="WARNING",
            message="Test warning",
            module="test_mod",
            operation="test"
        )
        json_str = entry.to_json()
        data = json.loads(json_str)
        
        assert data["level"] == "WARNING"
        assert data["message"] == "Test warning"
        assert data["module"] == "test_mod"
        assert data["operation"] == "test"
        assert "timestamp" in data
        assert "trace_id" in data
        # None values should be filtered out
        assert "success" not in data
        assert "duration_ms" not in data
        assert "error" not in data


class TestReproducibilityLogger:
    """Tests for ReproducibilityLogger class."""

    def test_init(self):
        """Test logger initialization."""
        logger = ReproducibilityLogger("test_name")
        assert logger.name == "test_name"

    def test_log_basic(self):
        """Test basic logging."""
        logger = ReproducibilityLogger("test")
        entry = logger.log("test_operation")
        assert isinstance(entry, LogEntry)
        assert entry.operation == "test_operation"

    def test_log_with_params(self):
        """Test logging with parameters."""
        logger = ReproducibilityLogger("test")
        entry = logger.log("op", param1="val1", param2=123)
        assert entry.parameters["param1"] == "val1"
        assert entry.parameters["param2"] == 123

    def test_info_method(self):
        """Test info method doesn't raise."""
        logger = ReproducibilityLogger("test")
        # Should not raise
        logger.info("test message")
        logger.info("test message", extra="data")

    def test_debug_method(self):
        """Test debug method doesn't raise."""
        logger = ReproducibilityLogger("test")
        logger.debug("debug message")

    def test_warning_method(self):
        """Test warning method doesn't raise."""
        logger = ReproducibilityLogger("test")
        logger.warning("warning message")

    def test_error_method(self):
        """Test error method doesn't raise."""
        logger = ReproducibilityLogger("test")
        logger.error("error message")

    def test_critical_method(self):
        """Test critical method doesn't raise."""
        logger = ReproducibilityLogger("test")
        logger.critical("critical message")

    def test_unknown_method(self):
        """Test that unknown methods return no-op."""
        logger = ReproducibilityLogger("test")
        # Should not raise, should return None
        result = logger.unknown_method("arg", kwarg="val")
        assert result is None

    def test_log_level_handling(self):
        """Test that level parameter is handled."""
        logger = ReproducibilityLogger("test")
        entry = logger.log("op", level="DEBUG")
        assert entry.level == "DEBUG"


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_no_args(self):
        """Test setup with no arguments."""
        logger = setup_logging()
        assert isinstance(logger, ReproducibilityLogger)

    def test_with_level(self):
        """Test setup with level argument."""
        logger = setup_logging(level="INFO")
        assert isinstance(logger, ReproducibilityLogger)

    def test_with_log_level(self):
        """Test setup with log_level argument."""
        logger = setup_logging(log_level="DEBUG")
        assert isinstance(logger, ReproducibilityLogger)

    def test_with_module_name(self):
        """Test setup with module_name argument."""
        logger = setup_logging(module_name="test_module")
        assert isinstance(logger, ReproducibilityLogger)

    def test_with_config(self):
        """Test setup with config dict."""
        config = {"log_file": "/tmp/test.log", "log_level": "WARNING"}
        logger = setup_logging(config=config)
        assert isinstance(logger, ReproducibilityLogger)

    def test_with_log_file(self):
        """Test setup with log_file argument."""
        logger = setup_logging(log_file="/tmp/custom.log")
        assert isinstance(logger, ReproducibilityLogger)

    def test_multiple_calls_return_same_instance(self):
        """Test that multiple calls return the same global logger."""
        logger1 = setup_logging()
        logger2 = setup_logging()
        assert logger1 is logger2


class TestLogOperation:
    """Tests for log_operation function."""

    def test_direct_call(self):
        """Test direct call returns LogEntry."""
        entry = log_operation("test_op", param="value")
        assert isinstance(entry, LogEntry)
        assert entry.operation == "test_op"
        assert entry.parameters["param"] == "value"

    def test_decorator(self):
        """Test decorator usage."""
        @log_operation
        def my_function(x, y):
            return x + y

        result = my_function(2, 3)
        assert result == 5

    def test_decorator_with_params(self):
        """Test decorator with parameters."""
        @log_operation("custom_op")
        def another_func(a):
            return a * 2

        result = another_func(5)
        assert result == 10


class TestLogWithExtra:
    """Tests for log_with_extra function."""

    def test_basic(self):
        """Test basic logging with extra fields."""
        # Should not raise
        log_with_extra("test message", level="INFO", extra_field="value")

    def test_with_error(self):
        """Test logging with error field."""
        log_with_extra("error occurred", level="ERROR", error_code=500)