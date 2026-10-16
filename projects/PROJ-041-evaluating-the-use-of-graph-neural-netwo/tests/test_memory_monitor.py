"""
Unit tests for the memory‑monitor utilities.

The tests verify that:
* ``run_with_limit`` raises ``MemoryLimitExceededError`` when the
  requested allocation exceeds the 7 GB hard limit.
* ``run_with_limit`` correctly executes a supplied callable when the
  allocation is within the limit.
"""

import pytest

from code.utils.memory_monitor import (
    MemoryLimitExceededError,
    run_with_limit,
)


def dummy_success():
    """A no‑op function that should succeed under the memory limit."""
    return "ok"


def test_run_with_limit_exceeds_hard_limit():
    """Requesting more than 7 GB must raise the custom error."""
    with pytest.raises(MemoryLimitExceededError):
        run_with_limit(8)  # 8 GB > 7 GB hard limit


def test_run_with_limit_executes_callable():
    """A callable that does nothing should run without error."""
    result = run_with_limit(1, dummy_success)  # 1 GB is well within the limit
    assert result == "ok"