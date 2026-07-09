"""
Tests for performance monitoring utilities (T026).
"""
import pytest
import time
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.performance_monitor import (
    enforce_time_limit,
    get_rss_mb,
    MAX_TIME_PER_SUBJECT_SECONDS,
    LOG_FILE
)

class TestPerformanceMonitor:
    """Test suite for performance monitoring functions."""
    
    def test_get_rss_mb_returns_positive(self):
        """Test that get_rss_mb returns a positive number."""
        rss = get_rss_mb()
        assert rss > 0, "RSS should be positive"
    
    def test_enforce_time_limit_success(self):
        """Test that enforce_time_limit allows fast operations to complete."""
        def fast_op():
            return {"status": "ok"}
        
        result = enforce_time_limit("sub-001", fast_op)
        assert result == {"status": "ok"}
    
    def test_enforce_time_limit_timeout(self):
        """Test that enforce_time_limit raises TimeoutError for slow operations."""
        def slow_op():
            time.sleep(1)  # Simulate slow operation
            return {"status": "ok"}
        
        # Patch the timeout to be very short for testing
        with patch('code.performance_monitor.MAX_TIME_PER_SUBJECT_SECONDS', 0.001):
            with pytest.raises(TimeoutError):
                enforce_time_limit("sub-002", slow_op)
    
    def test_log_entry_created_on_success(self):
        """Test that a log entry is created on successful completion."""
        def op():
            return {"status": "ok"}
        
        # Clear log file first
        if LOG_FILE.exists():
            LOG_FILE.unlink()
        
        enforce_time_limit("sub-003", op)
        
        assert LOG_FILE.exists(), "Log file should be created"
        with open(LOG_FILE, 'r') as f:
            logs = json.load(f)
        
        assert len(logs) > 0, "Log should have entries"
        assert any(entry['event'] == 'SUCCESS' for entry in logs)
    
    def test_log_entry_created_on_timeout(self):
        """Test that a log entry is created on timeout."""
        def slow_op():
            time.sleep(0.1)
            return {"status": "ok"}
        
        # Clear log file first
        if LOG_FILE.exists():
            LOG_FILE.unlink()
        
        with patch('code.performance_monitor.MAX_TIME_PER_SUBJECT_SECONDS', 0.001):
            try:
                enforce_time_limit("sub-004", slow_op)
            except TimeoutError:
                pass  # Expected
        
        assert LOG_FILE.exists(), "Log file should be created"
        with open(LOG_FILE, 'r') as f:
            logs = json.load(f)
        
        assert len(logs) > 0, "Log should have entries"
        assert any(entry['event'] == 'TIMEOUT' for entry in logs)
    
    def test_subject_id_in_log(self):
        """Test that subject_id is correctly logged."""
        def op():
            return {"status": "ok"}
        
        subject_id = "sub-test-123"
        if LOG_FILE.exists():
            LOG_FILE.unlink()
        
        enforce_time_limit(subject_id, op)
        
        with open(LOG_FILE, 'r') as f:
            logs = json.load(f)
        
        assert any(entry['subject_id'] == subject_id for entry in logs)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])