import os
import sys
import json
import time
import tempfile
import shutil
from pathlib import Path
import pytest

# Add code directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils import ResourceMonitor

class TestResourceMonitor:
    """
    Unit tests for the ResourceMonitor class.
    Tests instantiation, start/stop logic, and finalization with simulated memory usage.
    """

    def test_init_default(self):
        """Test initialization with default path."""
        monitor = ResourceMonitor()
        assert monitor.start_time is None
        assert monitor.end_time is None
        assert monitor.output_path == "data/processed/resource_profile.json"
        assert monitor._monitoring is False

    def test_init_custom_dir(self):
        """Test initialization with custom processed directory."""
        custom_dir = "/tmp/test_output"
        monitor = ResourceMonitor(processed_dir=custom_dir)
        expected_path = os.path.join(custom_dir, "resource_profile.json")
        assert monitor.output_path == expected_path

    def test_start_stop_logic(self):
        """Test that start and stop record times correctly."""
        monitor = ResourceMonitor()
        monitor.start()
        time.sleep(0.2) # Sleep briefly to simulate work
        monitor.stop()
        
        assert monitor.start_time is not None
        assert monitor.end_time is not None
        assert monitor.end_time >= monitor.start_time

    def test_finalize_creates_json(self):
        """Test that finalize writes the correct JSON structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor = ResourceMonitor(processed_dir=tmpdir)
            monitor.start()
            time.sleep(0.3) # Simulate some runtime
            monitor.stop()
            profile = monitor.finalize()
            
            # Check file exists
            output_path = Path(tmpdir) / "resource_profile.json"
            assert output_path.exists(), "resource_profile.json was not created"
            
            # Check content
            assert "peak_ram_gb" in profile
            assert "total_runtime_hours" in profile
            assert isinstance(profile["peak_ram_gb"], float)
            assert isinstance(profile["total_runtime_hours"], float)

    def test_simulated_memory_spike(self):
        """
        Simulates a scenario where memory usage spikes (e.g., 2GB) and verifies
        the monitor captures it.
        
        Note: Since we cannot easily force the OS to allocate exactly 2GB in a 
        unit test without side effects, we verify the logic by ensuring the 
        monitor runs, samples data (even if small), and correctly calculates 
        positive values. The 'simulation' here is the act of running the monitor
        during a small allocation loop to ensure the sampling mechanism works.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor = ResourceMonitor(processed_dir=tmpdir)
            
            # Start monitoring
            monitor.start()
            
            # Simulate memory usage by allocating a list of data
            # This ensures the process RSS increases slightly, which psutil should catch
            dummy_data = []
            try:
                # Allocate ~100MB to ensure a measurable spike if psutil is accurate
                # This is a safe, clean simulation of "work"
                for _ in range(10):
                    dummy_data.append([0.0] * (1024 * 1024)) 
                    time.sleep(0.05)
            finally:
                # Stop monitoring
                monitor.stop()
                # Clear data to free memory
                del dummy_data

            profile = monitor.finalize()

            # Assertions required by task:
            # The test MUST assert peak_ram_gb > 0 and total_runtime_hours > 0
            assert profile["peak_ram_gb"] > 0, f"Expected peak_ram_gb > 0, got {profile['peak_ram_gb']}"
            assert profile["total_runtime_hours"] > 0, f"Expected total_runtime_hours > 0, got {profile['total_runtime_hours']}"

            # Verify the JSON file content matches the return value
            output_path = Path(tmpdir) / "resource_profile.json"
            with open(output_path, 'r') as f:
                saved_profile = json.load(f)
            
            assert saved_profile["peak_ram_gb"] == profile["peak_ram_gb"]
            assert saved_profile["total_runtime_hours"] == profile["total_runtime_hours"]

    def test_finalize_without_start(self):
        """Test that finalize handles missing start/stop gracefully."""
        monitor = ResourceMonitor()
        # Do not call start/stop
        profile = monitor.finalize()
        
        assert "peak_ram_gb" in profile
        assert "total_runtime_hours" in profile
        # Runtime should be very small but non-negative
        assert profile["total_runtime_hours"] >= 0
        # RAM might be 0 if no samples were taken (psutil unavailable or no samples)
        # but the structure must be valid.
        assert isinstance(profile["peak_ram_gb"], float)
