from utils.logging import get_logger, log_operation

def test_get_logger_singleton():
    logger1 = get_logger("test")
    logger2 = get_logger()
    assert logger1 is logger2

def test_log_operation_direct():
    entry = log_operation("test_op", param=123)
    assert entry.operation == "test_op"
    assert entry.parameters["param"] == 123

def test_log_operation_decorator():
    @log_operation
    def add(a, b):
        return a + b
    assert add(2, 3) == 5
