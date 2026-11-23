import json
import os
import tempfile
import time
import pytest
from pathlib import Path

# Import the module under test
# Adjust import path based on project structure
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from logging_infrastructure import ResourceMonitor, setup_pipeline_logging


class TestResourceMonitor:
    def test_monitor_creates_file(self):
        """Test that the monitor creates the log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test.log")
            monitor = ResourceMonitor(log_path=log_path, interval_seconds=0.1)
            
            # File should not exist yet before start
            assert not os.path.exists(log_path)
            
            monitor.start()
            time.sleep(0.3) # Wait for at least one interval
            monitor.stop()
            
            assert os.path.exists(log_path)

    def test_monitor_logs_valid_json(self):
        """Test that the monitor writes valid JSON lines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test.log")
            monitor = ResourceMonitor(log_path=log_path, interval_seconds=0.1)
            
            monitor.start()
            time.sleep(0.3)
            monitor.stop()
            
            with open(log_path, "r") as f:
                lines = f.readlines()
            
            assert len(lines) > 0
            for line in lines:
                # Should not raise
                entry = json.loads(line)
                assert "timestamp" in entry
                assert "cpu_percent" in entry
                assert "ram_percent" in entry

    def test_monitor_stops_cleanly(self):
        """Test that the monitor thread stops cleanly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test.log")
            monitor = ResourceMonitor(log_path=log_path, interval_seconds=0.1)
            
            monitor.start()
            time.sleep(0.2)
            
            # Stop should return quickly
            monitor.stop()
            
            # Thread should be dead
            assert not monitor._thread.is_alive()


class TestSetupPipelineLogging:
    def test_setup_returns_monitor(self):
        """Test that setup_pipeline_logging returns a started monitor."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test.log")
            monitor = setup_pipeline_logging(log_path=log_path, interval=0.1)
            
            assert isinstance(monitor, ResourceMonitor)
            assert monitor._thread.is_alive()
            
            monitor.stop()

    def test_setup_creates_directories(self):
        """Test that setup_pipeline_logging creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a nested path that doesn't exist
            nested_path = os.path.join(tmpdir, "deep", "nested", "log.log")
            monitor = setup_pipeline_logging(log_path=nested_path, interval=0.1)
            
            assert os.path.exists(os.path.dirname(nested_path))
            
            monitor.stop()