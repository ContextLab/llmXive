"""Basic sanity test for the reproducibility logger contract."""

from utils.logger import get_logger, log_operation, LogEntry

def test_logger_basic_operations():
    logger = get_logger("test_logger")
    # Direct logging should return a LogEntry with to_json
    entry = log_operation("test_op", param=123)
    assert isinstance(entry, LogEntry)
    json_str = entry.to_json()
    assert "test_op" in json_str
    assert "param" in json_str

    # Decorator without args
    @log_operation
    def dummy_func(x):
        return x * 2

    assert dummy_func(3) == 6

    # Decorator with name argument
    @log_operation("named_op")
    def another_func(y):
        return y + 1

    assert another_func(5) == 6
    # The call should have logged an entry (no exception means tolerant) 
    # Retrieve the global logger and ensure an entry was added
    global_logger = get_logger()
    assert any(isinstance(e, LogEntry) and e.operation == "named_op" for e in global_logger.entries)