"""
Unit tests for the structured logging infrastructure.
"""
import logging
import json
import io
import sys
from unittest.mock import patch
import pytest

from utils.logging_config import (
    StructuredFormatter,
    ContextFilter,
    get_logger,
    configure_root_logger,
    log_info_with_context,
    log_warning_with_context,
    log_error_with_context
)


class TestStructuredFormatter:
    def test_format_produces_valid_json(self):
        """Test that the formatter produces valid JSON output."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        output = formatter.format(record)
        parsed = json.loads(output)

        assert "timestamp" in parsed
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Test message"
        assert parsed["module"] == "test"

    def test_format_includes_exception(self):
        """Test that exceptions are captured in the JSON output."""
        formatter = StructuredFormatter()
        try:
            raise ValueError("Test error")
        except ValueError:
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=1,
                msg="Error occurred",
                args=(),
                exc_info=sys.exc_info()
            )
            output = formatter.format(record)
            parsed = json.loads(output)
            assert parsed["exception"] is not None
            assert "ValueError" in parsed["exception"]


class TestContextFilter:
    def test_filter_injects_context(self):
        """Test that the filter injects global context into log records."""
        context = {"project_id": "PROJ-786", "run_id": "abc123"}
        log_filter = ContextFilter(context)

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None
        )

        log_filter.filter(record)

        assert hasattr(record, 'context')
        assert record.context["project_id"] == "PROJ-786"
        assert record.context["run_id"] == "abc123"

    def test_filter_merges_existing_context(self):
        """Test that the filter merges with existing context."""
        context = {"global_key": "global_value"}
        log_filter = ContextFilter(context)

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None
        )
        record.context = {"local_key": "local_value"}

        log_filter.filter(record)

        assert record.context["global_key"] == "global_value"
        assert record.context["local_key"] == "local_value"


class TestLoggingHelpers:
    def setup_method(self):
        """Setup: capture stdout for log inspection."""
        self.holder = io.StringIO()
        self.handler = logging.StreamHandler(self.holder)
        self.handler.setFormatter(StructuredFormatter())
        self.logger = get_logger("test_logger")
        self.logger.addHandler(self.handler)
        self.logger.setLevel(logging.INFO)

    def teardown_method(self):
        """Teardown: remove handler."""
        self.logger.removeHandler(self.handler)

    def test_log_info_with_context(self):
        """Test logging info with context."""
        log_info_with_context(
            self.logger,
            "Info message",
            context={"user": "alice", "action": "login"}
        )
        output = self.holder.getvalue()
        parsed = json.loads(output.strip())

        assert parsed["message"] == "Info message"
        assert parsed["context"]["user"] == "alice"
        assert parsed["context"]["action"] == "login"

    def test_log_warning_with_context(self):
        """Test logging warning with context."""
        log_warning_with_context(
            self.logger,
            "Warning message",
            context={"risk": "high"}
        )
        output = self.holder.getvalue()
        parsed = json.loads(output.strip())

        assert parsed["level"] == "WARNING"
        assert parsed["message"] == "Warning message"
        assert parsed["context"]["risk"] == "high"

    def test_log_error_with_context(self):
        """Test logging error with context."""
        log_error_with_context(
            self.logger,
            "Error message",
            context={"error_code": 500}
        )
        output = self.holder.getvalue()
        parsed = json.loads(output.strip())

        assert parsed["level"] == "ERROR"
        assert parsed["message"] == "Error message"
        assert parsed["context"]["error_code"] == 500
        assert "exception" in parsed
        assert parsed["exception"] is None  # exc_info=True but no exception raised in this test
