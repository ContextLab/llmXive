import pytest
from utils.logging import get_logger, log_operation, LogEntry

def test_logger_singleton():
    logger1 = get_logger(name="test1")
    logger2 = get_logger(name="test2")
    assert logger1 is logger2
    assert logger1.name == "test1"  # first call sets the name

def test_log_operation_decorator():
    @log_operation
    def add(a, b):
        return a + b

    result = add(2, 3)
    assert result == 5

def test_log_operation_direct():
    entry = log_operation("my_op", param=42)
    assert isinstance(entry, LogEntry)
    data = entry.to_json()
    assert '"operation": "my_op"' in data
    assert '"param": 42' in data

def test_logger_noop_methods():
    logger = get_logger()
    # These should not raise
    logger.info("info message")
    logger.debug("debug message")
    logger.warning("warn")
    logger.error("error")
    logger.critical("critical")