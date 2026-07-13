"""Unit tests for logging and retry logic."""
import sys
from pathlib import Path

# Ensure code directory is in path
current_dir = Path(__file__).parent.parent
if str(current_dir / "code") not in sys.path:
    sys.path.insert(0, str(current_dir / "code"))

from utils.logging import retry_on_failure, get_logger, LogEntry, log_operation


def test_retry_decorator_max_attempts():
    """Test retry with max_attempts."""
    call_count = 0

    @retry_on_failure(max_attempts=3, delay_seconds=0)
    def flaky_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Fail")
        return "Success"

    result = flaky_func()
    assert result == "Success"
    assert call_count == 3


def test_retry_decorator_max_retries():
    """Test retry with max_retries (alias)."""
    call_count = 0

    @retry_on_failure(max_retries=2, delay=0)
    def flaky_func2():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Fail")
        return "Success"

    result = flaky_func2()
    assert result == "Success"
    assert call_count == 3


def test_retry_exhausted_raises():
    """Test that retry exhausted raises the last exception."""
    @retry_on_failure(max_attempts=2, delay_seconds=0)
    def always_fail():
        raise ValueError("Always fails")

    try:
        always_fail()
        assert False, "Expected exception"
    except ValueError as e:
        assert str(e) == "Always fails"


def test_log_operation_direct_call():
    """Test log_operation as a direct call returns LogEntry."""
    entry = log_operation("test_op", param="value")
    assert isinstance(entry, LogEntry)
    assert entry.operation == "test_op"
    assert entry.parameters["param"] == "value"
    json_str = entry.to_json()
    assert "test_op" in json_str


def test_log_operation_decorator():
    """Test log_operation as a decorator."""
    @log_operation
    def my_func():
        return 42

    result = my_func()
    assert result == 42