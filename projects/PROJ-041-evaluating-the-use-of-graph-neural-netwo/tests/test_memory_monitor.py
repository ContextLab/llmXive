"""Tests for code/utils/memory_monitor.py."""

import sys
from pathlib import Path

import pytest

CODE_DIR = Path(__file__).resolve().parents[1] / "code"
sys.path.insert(0, str(CODE_DIR))

from utils.memory_monitor import MemoryLimitError, run_with_limit  # noqa: E402


def _allocate(n_bytes: int) -> int:
    buf = bytearray(n_bytes)
    return len(buf)


def test_run_with_limit_returns_result():
    result = run_with_limit(1.0, lambda a, b: a + b, 2, 3)
    assert result == 5


def test_run_with_limit_raises_on_exceeded_budget():
    # Allocate ~8 MB under a 1 MB (0.001 GB) budget -> must raise.
    with pytest.raises(MemoryLimitError):
        run_with_limit(0.001, _allocate, 8 * 1024 * 1024)


def test_memory_limit_error_is_runtime_error():
    assert issubclass(MemoryLimitError, RuntimeError)


def test_run_with_limit_stops_tracing_afterwards():
    import tracemalloc

    run_with_limit(1.0, _allocate, 1024)
    assert not tracemalloc.is_tracing()
