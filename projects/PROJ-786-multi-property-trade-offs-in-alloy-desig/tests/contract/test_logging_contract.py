"""
Contract tests for the logging infrastructure.
Ensures that all logging calls in the project produce structured JSON output.
"""
import logging
import json
import io
import sys
import re
from unittest.mock import patch

import pytest

from utils.logging_config import (
    StructuredFormatter,
    configure_root_logger,
    get_logger,
    log_info_with_context,
    log_warning_with_context,
    log_error_with_context
)


class TestLoggingContract:
    """
    Contract tests to ensure logging infrastructure meets project requirements.
    """

    def test_all_logs_are_json_structured(self):
        """
        Contract: All logs produced by the system must be valid JSON.
        """
        # Capture root logger output
        holder = io.StringIO()
        handler = logging.StreamHandler(holder)
        handler.setFormatter(StructuredFormatter())

        root_logger = logging.getLogger()
        original_handlers = root_logger.handlers[:]
        root_logger.handlers.clear()
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)

        try:
            # Trigger logs from various levels
            logger = get_logger("contract_test")
            log_info_with_context(logger, "Info log", context={"test": "info"})
            log_warning_with_context(logger, "Warning log", context={"test": "warn"})
            log_error_with_context(logger, "Error log", context={"test": "error"})

            output = holder.getvalue().strip()
            if output:
                for line in output.split('\n'):
                    if line:
                        # Must be valid JSON
                        parsed = json.loads(line)
                        assert "timestamp" in parsed
                        assert "level" in parsed
                        assert "message" in parsed
                        assert "context" in parsed
        finally:
            # Restore original handlers
            root_logger.handlers.clear()
            for h in original_handlers:
                root_logger.addHandler(h)

    def test_logs_include_required_fields(self):
        """
        Contract: Logs must include timestamp, level, message, module, and context.
        """
        holder = io.StringIO()
        handler = logging.StreamHandler(holder)
        handler.setFormatter(StructuredFormatter())

        logger = get_logger("contract_test")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        log_info_with_context(logger, "Test message", context={"key": "value"})

        output = holder.getvalue().strip()
        parsed = json.loads(output)

        required_fields = ["timestamp", "level", "message", "module", "context"]
        for field in required_fields:
            assert field in parsed, f"Missing required field: {field}"

    def test_context_is_always_present(self):
        """
        Contract: Every log entry must have a context field, even if empty.
        """
        holder = io.StringIO()
        handler = logging.StreamHandler(holder)
        handler.setFormatter(StructuredFormatter())

        logger = get_logger("contract_test")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # Log without explicit context
        logger.info("Message without context")

        output = holder.getvalue().strip()
        parsed = json.loads(output)

        assert "context" in parsed
        assert isinstance(parsed["context"], dict)

    def test_exception_logging_format(self):
        """
        Contract: When an exception is logged, it must be captured in the 'exception' field.
        """
        holder = io.StringIO()
        handler = logging.StreamHandler(holder)
        handler.setFormatter(StructuredFormatter())

        logger = get_logger("contract_test")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.ERROR)

        try:
            raise ValueError("Test exception")
        except ValueError:
            log_error_with_context(logger, "Error with exception", exc_info=True)

        output = holder.getvalue().strip()
        parsed = json.loads(output)

        assert "exception" in parsed
        assert parsed["exception"] is not None
        assert "ValueError" in parsed["exception"]
        assert "Test exception" in parsed["exception"]

    def test_log_levels_are_correct(self):
        """
        Contract: Log levels in output must match the actual log level used.
        """
        holder = io.StringIO()
        handler = logging.StreamHandler(holder)
        handler.setFormatter(StructuredFormatter())

        logger = get_logger("contract_test")
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        log_info_with_context(logger, "Info")
        log_warning_with_context(logger, "Warning")
        log_error_with_context(logger, "Error")

        output = holder.getvalue().strip()
        lines = output.split('\n')

        levels = [json.loads(line)["level"] for line in lines if line]

        assert "INFO" in levels
        assert "WARNING" in levels
        assert "ERROR" in levels