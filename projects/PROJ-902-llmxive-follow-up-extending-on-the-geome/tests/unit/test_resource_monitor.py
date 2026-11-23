"""
Unit tests for ``src.utils.resource_monitor.ResourceMonitor``.
The tests verify that the monitor records a non‑zero wall‑clock time
and that the reported peak RAM usage reflects memory allocations
performed inside the monitored block.
"""

import time

import pytest

from src.utils.resource_monitor import ResourceMonitor


@pytest.mark.timeout(30)
def test_resource_monitor_records_wall_clock_time():
    """
    The monitor should report a wall‑clock duration that matches the
    actual sleep time (within a small tolerance).
    """
    sleep_seconds = 2.0
    with ResourceMonitor() as rm:
        time.sleep(sleep_seconds)

    # Convert the expected duration to minutes.
    expected_minutes = sleep_seconds / 60.0
    # Allow a tolerance of 0.05 minutes (~3 seconds).
    tolerance = 0.05
    assert rm.wall_clock_min is not None, "wall_clock_min was not set"
    assert abs(rm.wall_clock_min - expected_minutes) < tolerance, (
        f"Expected ~{expected_minutes:.4f} min, got {rm.wall_clock_min:.4f} min"
    )


def test_resource_monitor_detects_memory_allocation():
    """
    Allocate a noticeable amount of memory inside the monitored block and
    ensure that ``peak_ram_gb`` is at least the size of the allocation.
    The allocation size is deliberately modest to keep the test fast
    and memory‑friendly.
    """
    # Roughly 20 MB of integers.
    num_ints = 5_000_000
    expected_gb = (num_ints * 8) / (1024 ** 3)  # 8 bytes per Python int (approx.)

    with ResourceMonitor() as rm:
        # Allocate memory.
        data = [0] * num_ints
        # Use the data so the interpreter does not optimise it away.
        _ = sum(data)

    assert rm.peak_ram_gb is not None, "peak_ram_gb was not set"
    # The monitor should report at least the expected allocation size,
    # allowing a small margin for interpreter overhead.
    margin = 0.01  # 10 MB margin
    assert rm.peak_ram_gb >= expected_gb - margin, (
        f"Peak RAM {rm.peak_ram_gb:.4f} GB is less than expected {expected_gb:.4f} GB"
    )
