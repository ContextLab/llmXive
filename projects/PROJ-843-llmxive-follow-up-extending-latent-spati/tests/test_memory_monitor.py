"""
Basic sanity‑check for the :class:`MemoryMonitor` utility.

The test verifies that:

* The monitor can be started and stopped without raising.
* A JSON log file is created at the supplied location.
* The log contains the expected keys and reasonable numeric values.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from utils.memory_monitor import MemoryMonitor


@pytest.fixture
def temp_log_path() -> Path:
    """Create a temporary file path for the memory‑monitor log."""
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)  # we only need the path, the monitor will write to it.
    yield Path(path)
    # Clean up after the test.
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def test_memory_monitor_writes_log(temp_log_path: Path):
    monitor = MemoryMonitor(output_path=temp_log_path)
    # Use the monitor as a context manager – this also exercises __enter__/__exit__.
    with monitor:
        # Simulate a small workload.
        total = sum(i * i for i in range(10_000))

    # After exiting the context manager the JSON log must exist.
    assert temp_log_path.is_file(), "MemoryMonitor did not create the log file"

    # Load and validate the JSON structure.
    with temp_log_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Expected keys.
    expected_keys = {"duration_seconds", "peak_ram_mb", "timestamp"}
    assert expected_keys.issubset(data.keys()), f"Missing keys in log: {expected_keys - data.keys()}"

    # Duration should be a positive number.
    assert isinstance(data["duration_seconds"], (int, float))
    assert data["duration_seconds"] > 0

    # Peak RAM may be zero if memory_profiler is unavailable; ensure it is numeric.
    assert isinstance(data["peak_ram_mb"], (int, float))
