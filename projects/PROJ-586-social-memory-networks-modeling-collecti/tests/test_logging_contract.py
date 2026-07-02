"""Basic sanity tests for the new logging implementation."""

from utils.logging import get_logger, log_operation, LogEntry


def test_logger_is_singleton():
    logger1 = get_logger("first")
    logger2 = get_logger("second")
    assert logger1 is logger2
    assert logger1.name == "first"  # name from first call is retained


def test_log_operation_decorator():
    @log_operation
    def add(a, b):
        return a + b

    result = add(2, 3)
    assert result == 5


def test_log_operation_direct():
    entry = log_operation("test_op", param=42)
    assert isinstance(entry, LogEntry)
    data = entry.to_json()
    assert '"operation": "test_op"' in data
    assert '"param": 42' in data


def test_logger_noop_methods():
    logger = get_logger()
    # These should not raise.
    logger.info("msg")
    logger.debug("msg")
    logger.warning("msg")
    logger.error("msg")
    logger.critical("msg")