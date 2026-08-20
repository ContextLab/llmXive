import json
import os
import sys
import time
import tempfile
import threading
from pathlib import Path
from collections import namedtuple
from unittest.mock import patch, MagicMock

import pytest

# Import the class under test
from code.utils import ResourceMonitor, ResourceUsage

# Define a local namedtuple to avoid brittle psutil._common imports
MockMem = namedtuple('MockMem', ['rss', 'vms'])

class MockProcess:
    """
    Mock psutil.Process to simulate memory usage without relying on real psutil internals.
    """
    def __init__(self, rss_bytes, vms_bytes):
        self._rss = rss_bytes
        self._vms = vms_bytes
        self._pid = 12345

    def memory_info(self):
        return MockMem(rss=self._rss, vms=self._vms)

    def cpu_percent(self):
        # Return a deterministic mock CPU percent
        return 42.0

    @property
    def pid(self):
        return self._pid

class TestResourceMonitor:
    """
    Unit tests for the ResourceMonitor class.
    """

    def test_init_default_path(self):
        """Test that default output path is set correctly."""
        monitor = ResourceMonitor()
        assert monitor.output_path == "data/processed/resource_profile.json"

    def test_init_custom_path(self):
        """Test that custom output path is set correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor = ResourceMonitor(processed_dir=tmpdir)
            expected = os.path.join(tmpdir, "resource_profile.json")
            assert monitor.output_path == expected

    def test_start_stop_finalize_with_mock(self):
        """
        Test the full lifecycle of the monitor using a MockProcess.
        Asserts that peak_ram_gb > 0 and total_runtime_hours > 0.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "resource_profile.json")
            monitor = ResourceMonitor(processed_dir=tmpdir)

            # Mock the _get_current_usage to return a fixed high memory usage
            # Simulate 2GB RSS
            mock_rss = 2 * 1024**3 
            mock_vms = 4 * 1024**3
            
            mock_process = MockProcess(mock_rss, mock_vms)

            # Patch psutil.Process to return our mock
            with patch('code.utils.psutil.Process', return_value=mock_process):
                monitor.start()
                
                # Let it run for a tiny bit to ensure start_time is set
                time.sleep(0.15) 
                
                monitor.stop()
                profile = monitor.finalize()

            # Verify the file was written
            assert os.path.exists(output_file), "Output JSON file was not created"

            # Verify content
            assert "peak_ram_gb" in profile
            assert "total_runtime_hours" in profile

            # Assertions from requirements
            assert profile["peak_ram_gb"] > 0, "Peak RAM must be greater than 0"
            assert profile["total_runtime_hours"] > 0, "Total runtime must be greater than 0"

            # Verify the calculated peak RAM is close to our mock (allow small float variance)
            # 2GB in GB
            expected_peak_gb = 2.0
            assert abs(profile["peak_ram_gb"] - expected_peak_gb) < 0.1, \
                f"Expected peak RAM ~{expected_peak_gb} GB, got {profile['peak_ram_gb']}"

    def test_finalize_creates_directory(self):
        """Test that finalize creates the parent directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = os.path.join(tmpdir, "sub", "dir")
            monitor = ResourceMonitor(processed_dir=subdir)
            
            # Mock start/stop times to avoid threading issues in test
            monitor.start_time = time.time()
            monitor.end_time = time.time() + 1
            monitor.usage_samples = [ResourceUsage(time.time(), 1.0, 10.0)]
            
            monitor.finalize()
            
            assert os.path.exists(monitor.output_path)

    def test_no_psutil_graceful_handling(self):
        """Test behavior when psutil is not available."""
        with patch('code.utils.psutil', None):
            monitor = ResourceMonitor()
            # Should not raise
            monitor.start()
            assert monitor.start_time is not None
            monitor.stop()
            profile = monitor.finalize()
            
            # With no psutil, peak_ram_gb should be 0.0
            assert profile["peak_ram_gb"] == 0.0
            assert profile["total_runtime_hours"] > 0