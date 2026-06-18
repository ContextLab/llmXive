"""Basic sanity tests for the reproducibility logging utilities."""

import builtins
import types
from pathlib import Path

import pytest

from reproducibility.logs import get_logger, log_operation, log_op, LogEntry, ReproducibilityLogger


def test_logger_is_singleton():
    logger1 = get_logger()
    logger2 = get_logger()
    assert logger1 is logger2
    assert isinstance(logger1, ReproducibilityLogger)


def test_log_operation_decorator():
    @log_operation
    def add(a, b):
        return a + b

    result = add(2, 3)
    assert result == 5

    # The decorator should not alter the function's return value.
    # It also should not raise.


def test_log_operation_direct_call():
    entry = log_operation("test_op", foo="bar")
    assert isinstance(entry, LogEntry)
    assert entry.operation == "test_op"
    assert entry.parameters == {"foo": "bar"}
    # Ensure the logger stored the entry.
    logger = get_logger()
    assert entry in logger.entries


def test_log_op_alias_behaves_like_log_operation():
    entry = log_op("alias_op", answer=42)
    assert isinstance(entry, LogEntry)
    assert entry.operation == "alias_op"
    assert entry.parameters == {"answer": 42}


def test_logger_tolerant_methods():
    logger = get_logger()
    # These methods do not exist on the stdlib logger; they should be no‑ops.
    for method in ["info", "debug", "warning", "error", "critical"]:
        # Should not raise
        getattr(logger, method)("test message")


def test_logger_to_json():
    entry = LogEntry(operation="json_test", parameters={"x": 1})
    json_str = entry.to_json()
    # The resulting string should be valid JSON and contain the fields.
    import json

    parsed = json.loads(json_str)
    assert parsed["operation"] == "json_test"
    assert parsed["parameters"]["x"] == 1