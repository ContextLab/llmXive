"""
test_memory_limits.py
---------------------

Ensures that ``run_with_limit`` raises ``MemoryLimitError`` when the
allowed memory limit is set lower than the observed peak usage.
"""

import pytest

from utils.memory_monitor import MemoryLimitError, run_with_limit


def _dummy_function():
    """A trivial function that allocates a tiny amount of memory."""
    a = [0] * 10
    return sum(a)


def test_memory_limit_error():
    """
    With a zero‑GB limit, any non‑zero memory usage should trigger
    ``MemoryLimitError``.
    """
    with pytest.raises(MemoryLimitError):
        run_with_limit(0.0, _dummy_function)
