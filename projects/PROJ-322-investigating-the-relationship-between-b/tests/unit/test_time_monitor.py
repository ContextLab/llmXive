"""
Unit tests for the time_monitor module (T030).

Tests:
- Initialization of the monitor.
- Warning trigger at 5 hours.
- Hard stop at 6 hours.
- Correctness of elapsed time calculation.
"""
import time
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure code is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.time_monitor import (
    initialize_runtime_monitor, 
    check_runtime_status, 
    get_elapsed_time_hours,
    get_runtime_limit_hours,
    get_warning_runtime_hours
)
from code.logging_config import get_logger

class TestTimeMonitor:
    
    def setup_method(self):
        """Reset state before each test."""
        # We need to reset the module-level globals
        import code.time_monitor as tm
        tm._START_TIME = None
        tm._LOGGER = None

    def test_initialization_sets_start_time(self):
        """Test that initialization records the start time."""
        initialize_runtime_monitor()
        assert get_elapsed_time_hours() > 0.0
        # Allow a tiny margin for execution time
        assert get_elapsed_time_hours() < 0.01 

    def test_no_warning_below_threshold(self, caplog):
        """Test that no warning is logged when runtime < 5 hours."""
        initialize_runtime_monitor()
        
        # Simulate 4.5 hours elapsed
        import code.time_monitor as tm
        tm._START_TIME = time.time() - (4.5 * 3600)
        
        with caplog.at_level("WARNING"):
            result = check_runtime_status()
            assert result is True
            # Check that no "Time Limit Warning" was logged
            warning_logs = [r for r in caplog.records if "Time Limit Warning" in r.message]
            assert len(warning_logs) == 0

    def test_warning_triggered_at_threshold(self, caplog):
        """Test that a warning is logged when runtime >= 5 hours."""
        initialize_runtime_monitor()
        
        # Simulate 5.0 hours elapsed
        import code.time_monitor as tm
        tm._START_TIME = time.time() - (5.0 * 3600)
        
        with caplog.at_level("WARNING"):
            result = check_runtime_status()
            assert result is True
            
            # Verify warning was logged
            warning_logs = [r for r in caplog.records if "Time Limit Warning" in r.message]
            assert len(warning_logs) == 1
            assert "MARKER: TIME_LIMIT_WARNING_TRIGGERED" in warning_logs[0].message

    def test_hard_stop_exceeded(self):
        """Test that SystemExit is raised when runtime >= 6 hours."""
        initialize_runtime_monitor()
        
        # Simulate 6.5 hours elapsed
        import code.time_monitor as tm
        tm._START_TIME = time.time() - (6.5 * 3600)
        
        with pytest.raises(SystemExit) as exc_info:
            check_runtime_status()
        
        assert "Hard stop" in str(exc_info.value)
        assert "limit" in str(exc_info.value).lower()

    def test_get_elapsed_time_accuracy(self):
        """Test that elapsed time calculation is accurate."""
        import code.time_monitor as tm
        tm._START_TIME = time.time()
        
        # Wait a tiny bit
        time.sleep(0.1)
        
        elapsed = get_elapsed_time_hours()
        expected_min = 0.1 / 3600.0
        expected_max = 0.2 / 3600.0 # Generous upper bound
        
        assert expected_min <= elapsed <= expected_max

    def test_uninitialized_returns_true(self):
        """Test that check returns True if not initialized."""
        import code.time_monitor as tm
        tm._START_TIME = None
        
        # Should not raise and should return True
        result = check_runtime_status()
        assert result is True
