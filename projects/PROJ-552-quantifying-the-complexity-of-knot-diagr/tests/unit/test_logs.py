"""Basic sanity tests for the logging utilities."""

from reproducibility.logs import get_logger, log_operation

def test_get_logger_is_singleton():
    logger1 = get_logger()
    logger2 = get_logger("some.module")
    assert logger1 is logger2

def test_log_operation_decorator():
    @log_operation("test_op", output_path_arg="output")
    def dummy_func(output):
        return "ok"

    result = dummy_func("tmp.txt")
    assert result == "ok"
    # The decorator should not raise – we trust the log file exists.
    # No further assertions needed for this lightweight test.