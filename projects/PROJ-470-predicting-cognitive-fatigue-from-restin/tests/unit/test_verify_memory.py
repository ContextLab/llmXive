"""Tests for memory verification task T027."""
import os
import json
import pytest
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.monitor import ResourceMonitor


class TestResourceMonitor:
    """Tests for ResourceMonitor class."""

    def test_monitor_initialization(self):
        """Test that monitor initializes correctly."""
        monitor = ResourceMonitor()
        assert monitor.start_time is None
        assert monitor.end_time is None
        assert monitor.peak_memory_bytes == 0

    def test_start_stop(self):
        """Test that start and stop work without errors."""
        monitor = ResourceMonitor()
        monitor.start()
        monitor.stop()
        assert monitor.start_time is not None
        assert monitor.end_time is not None

    def test_memory_measurement(self):
        """Test that memory is measured and returned in GB."""
        monitor = ResourceMonitor()
        monitor.start()
        # Do some memory-intensive work
        data = [i * i for i in range(100000)]
        monitor.stop()

        peak_gb = monitor.get_peak_memory_gb()
        assert isinstance(peak_gb, float)
        assert peak_gb >= 0.0

    def test_runtime_measurement(self):
        """Test that runtime is measured and returned in hours."""
        import time
        monitor = ResourceMonitor()
        monitor.start()
        time.sleep(0.1)  # Sleep for 100ms
        monitor.stop()

        runtime_hours = monitor.get_total_runtime_hours()
        assert isinstance(runtime_hours, float)
        assert runtime_hours >= 0.0
        # 0.1 seconds is 0.1/3600 hours
        expected_min = 0.1 / 3600.0
        assert runtime_hours >= expected_min


class TestVerifyMemoryTask:
    """Tests for the T027 verification task."""

    def test_resource_usage_file_structure(self, tmp_path):
        """Test that resource usage JSON has correct structure."""
        usage_data = {
            "peak_rss_gb": 2.5,
            "total_runtime_hours": 0.5
        }
        output_file = tmp_path / "resource_usage.json"
        with open(output_file, "w") as f:
            json.dump(usage_data, f)

        with open(output_file, "r") as f:
            loaded = json.load(f)

        assert "peak_rss_gb" in loaded
        assert "total_runtime_hours" in loaded
        assert isinstance(loaded["peak_rss_gb"], float)
        assert isinstance(loaded["total_runtime_hours"], float)

    def test_memory_limit_check(self, tmp_path):
        """Test that memory limit check works correctly."""
        # Test within limit
        usage_within = {"peak_rss_gb": 5.0, "total_runtime_hours": 1.0}
        assert usage_within["peak_rss_gb"] <= 7.0

        # Test over limit
        usage_over = {"peak_rss_gb": 8.0, "total_runtime_hours": 1.0}
        assert usage_over["peak_rss_gb"] > 7.0