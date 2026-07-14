"""
Verify that the tolerant logging implementation does not raise on any call pattern.
"""

import pytest
from code.logging_config import get_logger, log_operation

def test_logger_tolerant_calls():
    logger = get_logger("test")
    # Direct log call with operation name
    entry = logger.log("my_op", foo="bar")
    assert entry.operation == "my_op"
    assert entry.parameters["foo"] == "bar"

    # Using .info (should be a no‑op, returns None)
    assert logger.info("something") is None

    # Decorator usage
    @log_operation
    def add(a, b):
        return a + b

    assert add(2, 3) == 5