from utils.logging import get_logger, log_operation

def test_logger_singleton():
    logger1 = get_logger("test")
    logger2 = get_logger()
    assert logger1 is logger2

def test_log_operation_returns_entry():
    entry = log_operation("my_op", param=42)
    assert hasattr(entry, "to_json")
    json_str = entry.to_json()
    assert '"operation": "my_op"' in json_str

def test_log_decorator():
    @log_operation
    def add(a, b):
        return a + b
    assert add(2, 3) == 5