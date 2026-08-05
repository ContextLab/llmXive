"""Unit tests for the memory monitoring utilities.

The tests exercise the public API without requiring large amounts of RAM.
They use ``monkeypatch`` to adjust the configured memory limit so that both
the non‑error and error paths can be verified.
"""

from __future__ import annotations

import pytest

# Import the module under test
from code.memory_monitor import (
    get_current_memory_mb,
    check_memory_limit,
    setup_memory_monitoring,
    stop_memory_monitoring,
)
from code import config


def test_get_current_memory_mb_returns_float():
    """The function should always return a float representing MB."""
    mem_mb = get_current_memory_mb()
    assert isinstance(mem_mb, float)
    assert mem_mb > 0  # At least some memory is used by the process.


def test_check_memory_limit_no_error(monkeypatch):
    """When the usage is below the configured limit, no exception is raised."""
    # Set a very high limit to guarantee no error.
    monkeypatch.setattr(config, "get_memory_limit_mb", lambda: 10_000)
    # Should not raise.
    check_memory_limit()


def test_check_memory_limit_raises(monkeypatch):
    """When the usage exceeds the limit, ``MemoryError`` is raised."""
    # Force a tiny limit so that the current process exceeds it.
    monkeypatch.setattr(config, "get_memory_limit_mb", lambda: 0.1)
    with pytest.raises(MemoryError):
        check_memory_limit()


def test_setup_and_stop_memory_monitoring(monkeypatch):
    """The monitoring thread can be started and stopped cleanly."""
    # Use a generous limit to avoid spurious errors during the test.
    monkeypatch.setattr(config, "get_memory_limit_mb", lambda: 10_000)
    thread = setup_memory_monitoring(sample_interval=0.1)
    # Give the thread a moment to run at least once.
    import time

    time.sleep(0.3)
    # Stopping should not raise.
    stop_memory_monitoring(thread)
    assert not thread.is_alive()
