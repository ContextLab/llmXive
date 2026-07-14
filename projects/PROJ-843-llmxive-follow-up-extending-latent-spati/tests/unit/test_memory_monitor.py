import json
import os
import tempfile
from pathlib import Path

import pytest

# Import the class from the project code
from utils.memory_monitor import MemoryMonitor


def test_memory_monitor_writes_log_to_specified_path(tmp_path: Path):
    """
    Verify that ``MemoryMonitor`` creates a JSON log file at the location
    provided via ``output_path`` and that the file contains the expected
    keys.
    """
    log_file = tmp_path / "monitor_log.json"

    # Use the monitor as a context manager to ensure start/stop are called.
    with MemoryMonitor(output_path=log_file) as monitor:
        # Perform a trivial operation to have non‑zero duration.
        sum(i for i in range(10))

    # After exiting the context the file should exist.
    assert log_file.is_file(), "Log file was not created"

    # Load and inspect the JSON content.
    with log_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Expected keys
    expected_keys = {"duration_seconds", "peak_ram_mb", "timestamp"}
    assert expected_keys.issubset(data.keys()), f"Missing keys in log: {expected_keys - data.keys()}"

    # Basic sanity checks on values
    assert isinstance(data["duration_seconds"], (int, float)), "duration_seconds should be numeric"
    assert data["duration_seconds"] >= 0, "duration_seconds should be non‑negative"
    assert isinstance(data["peak_ram_mb"], (int, float)), "peak_ram_mb should be numeric"
    # peak_ram_mb may be 0 when memory_profiler is unavailable; that's acceptable.


def test_memory_monitor_defaults_to_memory_log(tmp_path: Path, monkeypatch):
    """
    When no explicit output path is given, the monitor should write to
    ``memory.log`` in the current working directory.
    """
    # Change cwd to a temporary directory
    monkeypatch.chdir(tmp_path)

    monitor = MemoryMonitor()
    monitor.start()
    # simple work
    _ = sum(i for i in range(5))
    monitor.stop()

    default_log = Path("memory.log")
    assert default_log.is_file(), "Default memory.log was not created"

    # Clean up
    default_log.unlink()