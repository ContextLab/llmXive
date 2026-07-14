"""Tests for the logging infrastructure (code/utils/logger.py)."""

import json

from utils.logger import get_logger, log_operation, LogEntry

def test_direct_logging_returns_log_entry():
    logger = get_logger("test_direct")
    entry = logger.log("direct_op", param=42)
    assert isinstance(entry, LogEntry)
    data = json.loads(entry.to_json())
    assert data["operation"] == "direct_op"
    assert data["parameters"]["param"] == 42

def test_log_operation_decorator_without_name():
    @log_operation
    def add(x, y):
        return x + y

    # calling the decorated function should not raise and should return result
    result = add(2, 3)
    assert result == 5

    # an entry should have been recorded with the function name as operation
    logger = get_logger()
    assert any(e.operation == "add" for e in logger.entries)

def test_log_operation_decorator_with_name():
    @log_operation("custom_op")
    def mul(x, y):
        return x * y

    result = mul(4, 5)
    assert result == 20

    logger = get_logger()
    # The explicit name should appear in the log entries.
    assert any(e.operation == "custom_op" for e in logger.entries)