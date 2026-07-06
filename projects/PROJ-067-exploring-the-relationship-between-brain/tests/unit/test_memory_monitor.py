"""
Unit test for memory monitor threshold violation (T012).
"""
import pytest
import os
from code.utils.memory_monitor import MemoryLimitExceededError, get_current_rss_bytes, check_memory_limit

def test_get_current_rss_bytes():
    """Test that we can retrieve current RSS without error."""
    rss = get_current_rss_bytes()
    assert isinstance(rss, int)
    assert rss > 0

def test_check_memory_limit_under_limit(monkeypatch):
    """Test check_memory_limit passes when under limit."""
    # Mock the limit to be very high so we don't fail
    monkeypatch.setattr("code.utils.memory_monitor.MAX_MEMORY_BYTES", 10 * 1024 * 1024 * 1024) # 10GB
    
    # This should not raise
    try:
        check_memory_limit()
    except MemoryLimitExceededError:
        pytest.fail("check_memory_limit raised unexpectedly when under limit")

def test_check_memory_limit_over_limit(monkeypatch):
    """Test check_memory_limit raises when over limit."""
    # Mock current RSS to be huge
    mock_rss = 8 * 1024 * 1024 * 1024 # 8GB
    # Mock limit to be lower than mock_rss
    monkeypatch.setattr("code.utils.memory_monitor.MAX_MEMORY_BYTES", 7 * 1024 * 1024 * 1024) # 7GB
    
    # We need to patch get_current_rss_bytes to return our mock
    # Note: The actual implementation reads from /proc, so we patch the function directly
    import code.utils.memory_monitor as mm
    
    original_get = mm.get_current_rss_bytes
    mm.get_current_rss_bytes = lambda: mock_rss
    
    with pytest.raises(MemoryLimitExceededError) as exc_info:
        mm.check_memory_limit()
    
    assert "Memory limit exceeded" in str(exc_info.value)
    
    # Restore
    mm.get_current_rss_bytes = original_get
