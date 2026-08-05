"""
Contract test: Verify that per-run resource limits enforce failure when exceeded.

This test ensures that the resource_monitor module correctly raises errors
when RAM usage exceeds 7 GB or wall-clock time exceeds 360 minutes,
validating the enforcement of Constitution Principle III and FR-007.
"""
import time
import pytest
from unittest.mock import patch, MagicMock
import os
import sys
from pathlib import Path

# Ensure the project root is in the path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.resource_monitor import ResourceMonitor, RAM_LIMIT_GB, WALL_CLOCK_LIMIT_MIN

# Constants for test thresholds (slightly above limits to ensure trigger)
TEST_RAM_LIMIT_GB = 7.0
TEST_WALL_CLOCK_LIMIT_MIN = 360.0

class TestPerRunResourceLimitsFailure:
    """Tests for failure conditions when resource limits are exceeded."""

    def test_raises_on_ram_exceeded(self):
        """
        Verify that ResourceMonitor raises an error when simulated RAM usage
        exceeds the 7 GB limit.
        """
        monitor = ResourceMonitor()
        monitor.start()
        
        # Simulate a scenario where RAM usage is reported as exceeding the limit
        # We patch the internal _get_peak_rss method to return a value > 7 GB
        excessive_rss_bytes = int((TEST_RAM_LIMIT_GB + 1.0) * 1024 * 1024 * 1024)
        
        with patch.object(monitor, '_get_peak_rss', return_value=excessive_rss_bytes):
            # Simulate some work
            time.sleep(0.1)
            monitor.stop()
            
            # The monitor should raise an error upon stop if limits are exceeded
            # depending on implementation, or we check the internal state.
            # Assuming the monitor raises on stop() or check() based on T042/T043 requirements.
            # If the implementation doesn't auto-raise on stop, we explicitly check.
            peak_gb = monitor.get_peak_ram_gb()
            assert peak_gb > TEST_RAM_LIMIT_GB, "Test setup failed: RAM not exceeding limit"
            
            # Trigger the validation that should raise
            with pytest.raises(RuntimeError) as exc_info:
                monitor.validate_limits()
            
            assert "RAM" in str(exc_info.value) or "7" in str(exc_info.value)

    def test_raises_on_wall_clock_exceeded(self):
        """
        Verify that ResourceMonitor raises an error when wall-clock time
        exceeds the 360 minute limit.
        """
        monitor = ResourceMonitor()
        monitor.start()
        
        # Simulate a scenario where wall-clock time is reported as exceeding the limit
        # We patch the _get_elapsed_minutes method to return a value > 360
        excessive_minutes = TEST_WALL_CLOCK_LIMIT_MIN + 1.0
        
        with patch.object(monitor, '_get_elapsed_minutes', return_value=excessive_minutes):
            # Simulate some work
            time.sleep(0.1)
            monitor.stop()
            
            elapsed = monitor.get_elapsed_minutes()
            assert elapsed > TEST_WALL_CLOCK_LIMIT_MIN, "Test setup failed: Time not exceeding limit"
            
            # Trigger the validation that should raise
            with pytest.raises(RuntimeError) as exc_info:
                monitor.validate_limits()
            
            assert "time" in str(exc_info.value).lower() or "360" in str(exc_info.value)

    def test_passes_when_within_limits(self):
        """
        Verify that ResourceMonitor does NOT raise an error when usage
        is within limits.
        """
        monitor = ResourceMonitor()
        monitor.start()
        
        # Simulate normal usage
        normal_rss_bytes = int((TEST_RAM_LIMIT_GB - 1.0) * 1024 * 1024 * 1024)
        normal_minutes = 10.0
        
        with patch.object(monitor, '_get_peak_rss', return_value=normal_rss_bytes):
            with patch.object(monitor, '_get_elapsed_minutes', return_value=normal_minutes):
                time.sleep(0.1)
                monitor.stop()
                
                # Should not raise
                monitor.validate_limits()

    def test_failure_message_includes_limit_details(self):
        """
        Verify that the error message includes specific details about the
        exceeded limit to aid debugging.
        """
        monitor = ResourceMonitor()
        monitor.start()
        
        excessive_rss_bytes = int((TEST_RAM_LIMIT_GB + 2.0) * 1024 * 1024 * 1024)
        
        with patch.object(monitor, '_get_peak_rss', return_value=excessive_rss_bytes):
            time.sleep(0.1)
            monitor.stop()
            
            with pytest.raises(RuntimeError) as exc_info:
                monitor.validate_limits()
            
            error_msg = str(exc_info.value)
            # Check that the error message contains relevant info
            assert "7" in error_msg or "GB" in error_msg or "RAM" in error_msg