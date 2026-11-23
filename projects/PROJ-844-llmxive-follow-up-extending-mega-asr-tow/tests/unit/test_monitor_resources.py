"""
Unit tests for code/monitor_resources.py
"""
import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from monitor_resources import ResourceMonitor

def test_resource_monitor_creation():
    """Test ResourceMonitor initialization."""
    monitor = ResourceMonitor()
    assert monitor is not None
    assert monitor.start_time is None
    assert monitor.peak_rss is None

def test_monitor_start_stop():
    """Test starting and stopping monitoring."""
    monitor = ResourceMonitor()
    
    monitor.start()
    assert monitor.start_time is not None
    
    monitor.stop()
    assert monitor.peak_rss is not None

def test_monitor_context_manager():
    """Test using ResourceMonitor as context manager."""
    with ResourceMonitor() as monitor:
        # Do some work
        _ = sum(range(1000))
    
    assert monitor.start_time is not None
    assert monitor.peak_rss is not None
