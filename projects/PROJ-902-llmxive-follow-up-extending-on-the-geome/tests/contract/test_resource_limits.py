"""
Contract test for resource limits enforcement.

This test verifies that the resource_monitor module raises a ValueError
if the monitored RAM exceeds 7 GB or the wall-clock time exceeds 360 minutes (21,600 seconds).
"""

import pytest
import time
from unittest.mock import patch, MagicMock

# Import the resource monitor module
# Based on T008 implementation, the module is at code/src/utils/resource_monitor.py
# We import the specific functions needed for testing
from code.src.utils.resource_monitor import ResourceMonitor, check_resource_limits

# Constants matching the project requirements
RAM_LIMIT_GB = 7.0
WALL_CLOCK_LIMIT_MIN = 360
WALL_CLOCK_LIMIT_SEC = WALL_CLOCK_LIMIT_MIN * 60


class TestResourceLimitsContract:
    """Tests ensuring the resource monitor enforces strict limits."""

    def test_ram_limit_not_exceeded(self):
        """Test that no error is raised when RAM is within the limit."""
        # Simulate a peak RAM usage of 6.5 GB
        peak_ram_gb = 6.5
        wall_clock_sec = 1000

        # This should NOT raise an exception
        result = check_resource_limits(peak_ram_gb, wall_clock_sec)
        assert result is None

    def test_ram_limit_exceeded_raises_error(self):
        """Test that a ValueError is raised when RAM exceeds 7 GB."""
        # Simulate a peak RAM usage of 7.1 GB
        peak_ram_gb = 7.1
        wall_clock_sec = 1000

        with pytest.raises(ValueError) as exc_info:
            check_resource_limits(peak_ram_gb, wall_clock_sec)

        assert "RAM limit exceeded" in str(exc_info.value)
        assert "7.0" in str(exc_info.value)

    def test_wall_clock_limit_not_exceeded(self):
        """Test that no error is raised when wall-clock time is within the limit."""
        peak_ram_gb = 5.0
        # 359 minutes
        wall_clock_sec = 359 * 60

        result = check_resource_limits(peak_ram_gb, wall_clock_sec)
        assert result is None

    def test_wall_clock_limit_exceeded_raises_error(self):
        """Test that a ValueError is raised when wall-clock time exceeds 360 minutes."""
        peak_ram_gb = 5.0
        # 361 minutes
        wall_clock_sec = 361 * 60

        with pytest.raises(ValueError) as exc_info:
            check_resource_limits(peak_ram_gb, wall_clock_sec)

        assert "Wall-clock time limit exceeded" in str(exc_info.value)
        assert "360" in str(exc_info.value)

    def test_both_limits_exceeded_raises_error(self):
        """Test that a ValueError is raised when both RAM and wall-clock limits are exceeded."""
        peak_ram_gb = 8.0
        wall_clock_sec = 400 * 60

        with pytest.raises(ValueError) as exc_info:
            check_resource_limits(peak_ram_gb, wall_clock_sec)

        # The error message should indicate a limit violation
        assert "limit exceeded" in str(exc_info.value).lower()

    def test_monitor_class_integration(self):
        """Test that the ResourceMonitor class raises errors on stop() if limits are breached."""
        # Create a monitor instance
        monitor = ResourceMonitor()

        # Mock the internal tracking to simulate limit breaches
        # We patch the _peak_ram_gb and _start_time attributes directly for testing
        monitor._peak_ram_gb = 7.5  # Exceeds 7 GB
        monitor._start_time = time.time() - (361 * 60)  # Exceeds 360 min

        # Mock the _record_peak_ram to avoid actual system calls during this test
        with patch.object(monitor, '_record_peak_ram'):
            with pytest.raises(ValueError) as exc_info:
                monitor.stop()

            assert "limit exceeded" in str(exc_info.value).lower()

    def test_monitor_class_integration_within_limits(self):
        """Test that the ResourceMonitor class does NOT raise errors when within limits."""
        monitor = ResourceMonitor()

        # Set values within limits
        monitor._peak_ram_gb = 6.0
        monitor._start_time = time.time() - (300 * 60)

        with patch.object(monitor, '_record_peak_ram'):
            # This should complete without raising an exception
            monitor.stop()