"""Contract test for the shared logger implementation."""

from utils.logger import get_logger, log_operation, ReproducibilityLogger

def test_logger_is_singleton():
    logger1 = get_logger("first")
    logger2 = get_logger("second")
    assert logger1 is logger2
    assert isinstance(logger1, ReproducibilityLogger)

def test_log_operation_direct_call():
    entry = log_operation("test_op", foo="bar")
    assert entry.operation == "test_op"
    assert entry.parameters["foo"] == "bar"
    # Ensure JSON serialisation works
    json_str = entry.to_json()
    assert isinstance(json_str, str)

def test_log_operation_decorator():
    @log_operation
    def add(a, b):
        return a + b

    assert add(2, 3) == 5