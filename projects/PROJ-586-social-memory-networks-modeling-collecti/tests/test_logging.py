import pytest
from utils.logging import get_logger, log_operation, LogEntry

def test_logger_singleton():
    logger1 = get_logger()
    logger2 = get_logger(name="another")
    assert logger1 is logger2

def test_log_operation_decorator():
    @log_operation
    def add(a, b):
        return a + b

    result = add(2, 3)
    assert result == 5

def test_log_operation_direct():
    entry = log_operation("my_op", param=42)
    assert isinstance(entry, LogEntry)
    data = json.loads(entry.to_json())
    assert data["operation"] == "my_op"
    assert data["parameters"]["param"] == 42
