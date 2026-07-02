"""Simple sanity test to ensure the tolerant logger works with all call patterns."""
from utils.logging import get_logger, log_operation

def test_logger_various_calls():
    logger = get_logger("test_logger")
    # Direct logging
    entry = logger.log("test_op", param=123)
    assert entry.operation == "test_op"
    assert entry.parameters["param"] == 123

    # Shortcut via helper
    entry2 = log_operation("another_op", foo="bar")
    assert entry2.operation == "another_op"
    assert entry2.parameters["foo"] == "bar"

    # Logger‑style convenience methods (should be no‑ops, not raise)
    logger.info("info message")
    logger.debug("debug message", extra=5)
    logger.warning("warn")
    # Ensure they return None
    assert logger.info("msg") is None
    assert logger.debug("msg") is None
    assert logger.warning("msg") is None