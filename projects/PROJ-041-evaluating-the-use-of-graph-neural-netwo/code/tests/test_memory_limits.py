import pytest
from utils.memory_monitor import MemoryLimitError, run_with_limit

def _dummy_function():
    # Allocate a tiny amount of memory
    a = [0] * 10
    return sum(a)

def test_memory_limit_error():
    # With a zero‑GB limit, any allocation should trigger the error
    with pytest.raises(MemoryLimitError):
        run_with_limit(0, _dummy_function)