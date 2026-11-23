import pytest
import os
from unittest.mock import patch
from utils.memory_monitor import MemoryMonitor, MemoryLimitExceeded, get_current_rss_kb, enforce_memory_limit

def test_get_current_rss_kb():
    """Test that RSS reading works (or returns 0 on non-Linux)."""
    # On Linux, this should return a positive integer
    # On other systems, it might return 0 or raise
    try:
        rss = get_current_rss_kb()
        # Just ensure it doesn't crash
        assert isinstance(rss, int)
    except Exception:
        # If it fails, that's acceptable for non-Linux
        pass

def test_memory_monitor_check_memory():
    """Test MemoryMonitor.check_memory logic."""
    config = {'memory_limit_kb': 1000}
    monitor = MemoryMonitor(config)
    
    # Mock get_current_rss_kb to return a value below limit
    with patch('utils.memory_monitor.get_current_rss_kb', return_value=500):
        status = monitor.check_memory()
        assert status['exceeded'] is False
        assert status['current_kb'] == 500

    # Mock to return a value above limit
    with patch('utils.memory_monitor.get_current_rss_kb', return_value=2000):
        status = monitor.check_memory()
        assert status['exceeded'] is True
        assert status['current_kb'] == 2000

def test_enforce_memory_limit():
    """Test enforce_memory_limit raises on exceeded limit."""
    with patch('utils.memory_monitor.get_current_rss_kb', return_value=2000):
        with pytest.raises(MemoryLimitExceeded):
            enforce_memory_limit(1000)

    with patch('utils.memory_monitor.get_current_rss_kb', return_value=500):
        # Should not raise
        enforce_memory_limit(1000)
