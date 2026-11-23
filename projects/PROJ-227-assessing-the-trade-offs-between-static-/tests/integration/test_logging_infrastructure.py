"""
Integration tests for the logging infrastructure.

Verifies that the ResourceMonitor correctly logs CPU/RAM metrics
to a JSON Lines file with thread-safe writes.
"""

import json
import os
import tempfile
import time
from pathlib import Path

import pytest

from code.logging_infrastructure import ResourceMonitor, LOGS_DIR, LOG_FILE


@pytest.fixture
def temp_log_dir():
    """Creates a temporary directory for log files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_resource_monitor_logs_metrics(temp_log_dir):
    """Test that the monitor logs metrics to a file with correct schema."""
    log_file = temp_log_dir / "test_pipeline.log"
    lock_file = temp_log_dir / ".test_pipeline.log.lock"

    monitor = ResourceMonitor(interval=1.0, log_file=log_file)
    # Override the lock file path for the test
    monitor.lock_file = lock_file

    try:
        monitor.start()
        # Wait for at least 2 log entries (interval is 1.0s)
        time.sleep(2.5)
    finally:
        monitor.stop()

    assert log_file.exists(), "Log file should be created"

    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    assert len(lines) >= 2, f"Expected at least 2 log entries, got {len(lines)}"

    required_keys = {"timestamp", "cpu_percent", "ram_percent", "pid"}
    for i, line in enumerate(lines):
        try:
            entry = json.loads(line)
            assert required_keys.issubset(entry.keys()), f"Entry {i} missing required keys"
            assert isinstance(entry["timestamp"], str), f"Entry {i} timestamp should be string"
            assert isinstance(entry["cpu_percent"], (int, float)), f"Entry {i} cpu_percent should be numeric"
            assert isinstance(entry["ram_percent"], (int, float)), f"Entry {i} ram_percent should be numeric"
            assert isinstance(entry["pid"], int), f"Entry {i} pid should be int"
        except json.JSONDecodeError:
            pytest.fail(f"Entry {i} is not valid JSON: {line}")


def test_concurrent_writes(temp_log_dir):
    """Test that concurrent writes do not corrupt the log file."""
    log_file = temp_log_dir / "concurrent_test.log"
    lock_file = temp_log_dir / ".concurrent_test.log.lock"

    monitor = ResourceMonitor(interval=0.5, log_file=log_file)
    monitor.lock_file = lock_file

    # Start multiple monitors to simulate concurrent access
    monitors = []
    for _ in range(3):
        m = ResourceMonitor(interval=0.5, log_file=log_file)
        m.lock_file = lock_file
        monitors.append(m)
        m.start()

    try:
        time.sleep(3.0)
    finally:
        for m in monitors:
            m.stop()

    assert log_file.exists(), "Log file should be created"

    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Verify all lines are valid JSON
    for i, line in enumerate(lines):
        try:
            json.loads(line)
        except json.JSONDecodeError:
            pytest.fail(f"Corrupted entry at line {i}: {line}")