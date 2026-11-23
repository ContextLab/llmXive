"""
Unit tests for the Performance Monitor and Isolate Limit enforcement.
"""
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.performance_monitor import PerformanceMonitor, enforce_isolate_limit
from utils.config import get_max_isolates

class TestPerformanceMonitor:
    
    def test_init_default_limit(self):
        """Test that the monitor initializes with the config limit."""
        with patch('utils.performance_monitor.get_max_isolates', return_value=1000):
            monitor = PerformanceMonitor()
            assert monitor.max_isolates == 1000

    def test_init_custom_limit(self):
        """Test that the monitor accepts a custom limit."""
        monitor = PerformanceMonitor(max_isolates=500)
        assert monitor.max_isolates == 500

    def test_check_isolate_count_pass(self):
        """Test that count <= limit passes silently."""
        monitor = PerformanceMonitor(max_isolates=1000)
        # Should not raise
        monitor.check_isolate_count(1000, "test")
        monitor.check_isolate_count(500, "test")
        monitor.check_isolate_count(1, "test")

    def test_check_isolate_count_fail(self):
        """Test that count > limit raises ValueError."""
        monitor = PerformanceMonitor(max_isolates=1000)
        with pytest.raises(ValueError) as exc_info:
            monitor.check_isolate_count(1001, "test")
        assert "exceeds" in str(exc_info.value)
        assert "1001" in str(exc_info.value)
        assert "1000" in str(exc_info.value)

    def test_time_limit_check(self):
        """Test time limit checking logic."""
        monitor = PerformanceMonitor()
        monitor.start()
        
        # Mock time to simulate exceeding limit
        with patch('utils.performance_monitor.time.time', return_value=monitor.start_time + 7 * 3600):
            with pytest.raises(TimeoutError):
                monitor.check_time_limit(limit_hours=6.0)

        # Mock time to simulate warning
        with patch('utils.performance_monitor.time.time', return_value=monitor.start_time + 5.5 * 3600):
            # Should not raise, but might log warning (we don't test logs here)
            monitor.check_time_limit(limit_hours=6.0)

    def test_enforce_isolate_limit_function(self):
        """Test the convenience function."""
        enforce_isolate_limit(100, 1000)  # Pass
        with pytest.raises(ValueError):
            enforce_isolate_limit(1001, 1000)

class TestCIConstraintEnforcement:
    """
    Tests specifically for the N=1000 CI constraint requirement (T038).
    """
    
    def test_ci_limit_is_1000(self):
        """Verify the default CI limit is 1000."""
        # Assuming config defaults to 1000 for CI as per spec
        # If the config file overrides this, the test environment should reflect that.
        limit = get_max_isolates()
        assert limit == 1000, f"CI Limit should be 1000, got {limit}"

    def test_pipeline_rejects_large_dataset(self):
        """
        Simulate a pipeline step that tries to process 5000 isolates.
        The PerformanceMonitor must reject this to protect the 6-hour constraint.
        """
        monitor = PerformanceMonitor(max_isolates=1000)
        
        # Simulate ingestion reporting 5000 isolates
        raw_count = 5000
        
        with pytest.raises(ValueError) as e:
            monitor.check_isolate_count(raw_count, "Ingestion Phase")
        
        assert "5000" in str(e.value)
        assert "1000" in str(e.value)
        assert "6-hour" in str(e.value) or "constraint" in str(e.value).lower()

    def test_boundary_condition(self):
        """Test exactly at the limit."""
        monitor = PerformanceMonitor(max_isolates=1000)
        # 1000 should be allowed
        monitor.check_isolate_count(1000, "Boundary Test")
        
        # 1001 must fail
        with pytest.raises(ValueError):
            monitor.check_isolate_count(1001, "Boundary Test")