import time
from pathlib import Path

import pytest

from utils.memory_monitor import MemoryMonitor


def test_memory_monitor_writes_summary_and_log(tmp_path: Path):
    """
    Verify that MemoryMonitor records data, writes a detailed log and a summary
    JSON file, and that the recorded duration is positive.
    """
    log_file = tmp_path / "mem.log"
    monitor = MemoryMonitor(log_path=log_file, interval=0.05)

    # Use the context manager for simplicity.
    with monitor:
        # Simulate some work.
        time.sleep(0.2)

    # After exiting the context the monitor should have stopped and written files.
    summary_file = log_file.with_name(log_file.stem + "_summary.json")

    # Both files must exist.
    assert log_file.is_file(), "Detailed memory log not created"
    assert summary_file.is_file(), "Summary JSON not created"

    # Load and inspect the summary.
    import json
    with summary_file.open() as f:
        summary = json.load(f)

    assert isinstance(summary.get("peak_memory_mb"), (int, float)), "Peak memory missing"
    # Duration should be at least the sleep time (allow small tolerance).
    assert summary.get("duration_seconds", 0) >= 0.15, "Duration too short"

    # Ensure the log contains at least one record.
    with log_file.open() as f:
        lines = f.readlines()
    assert len(lines) > 0, "Memory log is empty"

# Ensure that calling an undefined attribute does not raise.
def test_memory_monitor_noop_attribute():
    monitor = MemoryMonitor()
    # These calls should be no‑ops and not raise AttributeError.
    monitor.info("test")
    monitor.debug("debug message")
    monitor.custom_method(123, key="value")
    # No assertion needed – the test passes if no exception is raised.