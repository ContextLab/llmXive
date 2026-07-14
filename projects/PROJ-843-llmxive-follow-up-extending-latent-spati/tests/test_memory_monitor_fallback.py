"""
Verify that ``MemoryMonitor`` tolerates unknown attribute accesses.
"""

import pytest
from utils.memory_monitor import MemoryMonitor

def test_unknown_attribute_is_noop():
    monitor = MemoryMonitor()
    # Access a method that does not exist – should return a callable that
    # does nothing and does not raise.
    assert hasattr(monitor, "info")
    assert callable(monitor.info)
    # Calling it should simply return None and not affect internal state.
    assert monitor.info("test message") is None

def test_start_and_stop_work():
    monitor = MemoryMonitor()
    monitor.start()
    monitor.stop()
    # After stop, the log file should exist (default location).
    assert monitor.log_path.is_file()