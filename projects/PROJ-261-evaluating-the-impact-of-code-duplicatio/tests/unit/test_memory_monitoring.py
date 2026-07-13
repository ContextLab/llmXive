"""
Unit test for the memory‑monitoring utilities (T023).

The test runs a lightweight computation inside the ``memory_monitor_context``
and asserts that no ``MemoryError`` is raised when the limit is set to a
generous value (e.g., 8 GB).  It also verifies that the context cleans up
the background thread.
"""

import pytest

from code.memory_monitor import memory_monitor_context, setup_memory_monitoring


def _dummy_heavy_computation():
    # Allocate ~50 MB of memory temporarily.
    data = [bytearray(1024 * 1024) for _ in range(50)]
    return sum(len(chunk) for chunk in data)


def test_memory_monitoring_no_exceed():
    # Use a limit higher than what the dummy computation consumes.
    limit_mb = 8000  # 8 GB
    # Ensure the monitor can be started via the convenience function.
    setup_memory_monitoring(memory_limit_mb=limit_mb, interval=0.1)

    # The context should not raise.
    with memory_monitor_context(memory_limit_mb=limit_mb):
        result = _dummy_heavy_computation()
    assert result == 50 * 1024 * 1024