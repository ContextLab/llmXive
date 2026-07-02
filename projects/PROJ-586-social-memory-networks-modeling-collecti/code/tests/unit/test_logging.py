from utils.logging import get_logger, log_operation
      
def test_logger_singleton():
    logger1 = get_logger(name="test1")
    logger2 = get_logger(name="test2")
    assert logger1 is logger2

def test_log_operation_decorator():
    @log_operation
    def add(a, b):
        return a + b

    result = add(2, 3)
    assert result == 5

def test_direct_log_returns_entry():
    entry = log_operation("test_op", param=42)
    assert hasattr(entry, "to_json")
    json_str = entry.to_json()
    assert '"operation": "test_op"' in json_str