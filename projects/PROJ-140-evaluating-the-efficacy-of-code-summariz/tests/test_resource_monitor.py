"""
Unit tests for code/utils/resource_monitor.py
"""

import time
import threading
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.resource_monitor import (
    start_monitoring,
    stop_monitoring,
    check_runtime_safely,
    get_status_report,
    MAX_RAM_GB,
    MAX_RUNTIME_HOURS,
    _monitor_active,
    _start_time,
    _peak_rss,
    _monitor_thread,
    _stop_event
)

# Reset module state before tests if necessary
def reset_monitor_state():
    """Helper to reset global state for testing."""
    global _monitor_active, _start_time, _peak_rss, _monitor_thread, _stop_event
    if _monitor_thread and _monitor_thread.is_alive():
        _stop_event.set()
        _monitor_thread.join(timeout=1.0)
    _monitor_active = False
    _start_time = None
    _peak_rss = 0
    _monitor_thread = None
    _stop_event = threading.Event()

@pytest.fixture(autouse=True)
def setup_teardown():
    reset_monitor_state()
    yield
    reset_monitor_state()

def test_start_monitoring():
    """Test that start_monitoring initializes state correctly."""
    start_monitoring()
    assert _monitor_active is True
    assert _start_time is not None
    assert _monitor_thread is not None
    assert _monitor_thread.is_alive()

def test_stop_monitoring_success():
    """Test that stop_monitoring passes when constraints are met."""
    start_monitoring()
    time.sleep(0.5)
    # Should not raise
    stop_monitoring()
    assert _monitor_active is False

def test_check_runtime_safely():
    """Test runtime safety check."""
    assert check_runtime_safely() is True  # Not started yet
    start_monitoring()
    time.sleep(0.1)
    assert check_runtime_safely() is True

def test_get_status_report():
    """Test status report generation."""
    start_monitoring()
    time.sleep(0.1)
    status = get_status_report()

    assert "peak_rss_kb" in status
    assert "current_rss_kb" in status
    assert "peak_ram_gb" in status
    assert "runtime_seconds" in status
    assert "constraints" in status
    assert status["constraints"]["max_ram_gb"] == MAX_RAM_GB
    assert status["constraints"]["max_runtime_hours"] == MAX_RUNTIME_HOURS

def test_monitor_thread_daemon():
    """Test that the monitor thread is a daemon."""
    start_monitoring()
    assert _monitor_thread.daemon is True