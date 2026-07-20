"""
Unit tests for the Resource Monitor module.
"""
import os
import json
import time
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Import the module under test
# Note: We assume the test is run from the project root or code/ is in path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from resource_monitor import ResourceMonitor, monitor_agent_run


class TestResourceMonitor:
    """Tests for the ResourceMonitor class."""

    def test_init(self):
        """Test initialization of ResourceMonitor."""
        monitor = ResourceMonitor("test_run_1")
        assert monitor.run_id == "test_run_1"
        assert monitor.start_time is None
        assert monitor.end_time is None
        assert monitor.peak_memory_mb == 0.0
        assert monitor.peak_cpu_percent == 0.0
        assert "platform" in monitor.system_info

    def test_start(self):
        """Test starting the monitor."""
        monitor = ResourceMonitor("test_run_2")
        monitor.start()
        assert monitor.start_time is not None
        assert len(monitor.cpu_samples) == 0

    def test_stop(self):
        """Test stopping the monitor calculates duration."""
        monitor = ResourceMonitor("test_run_3")
        monitor.start()
        time.sleep(0.1)
        monitor.stop()
        
        assert monitor.end_time is not None
        assert monitor.duration_seconds > 0
        assert hasattr(monitor, 'metrics')

    def test_sample(self):
        """Test sampling resources."""
        monitor = ResourceMonitor("test_run_4")
        monitor.start()
        
        # Perform a sample
        monitor.sample()
        
        # Peak memory should be >= 0 (even if fallback is used)
        assert monitor.peak_memory_mb >= 0
        
        monitor.stop()

    def test_get_metrics_dict(self):
        """Test retrieving metrics as a dictionary."""
        monitor = ResourceMonitor("test_run_5")
        monitor.start()
        time.sleep(0.1)
        monitor.stop()
        
        metrics = monitor.get_metrics_dict()
        
        assert isinstance(metrics, dict)
        assert metrics['run_id'] == "test_run_5"
        assert 'duration_seconds' in metrics
        assert 'peak_memory_mb' in metrics
        assert 'peak_cpu_percent' in metrics
        assert 'system_info' in metrics

    def test_save_report(self):
        """Test saving the report to a JSON file."""
        monitor = ResourceMonitor("test_run_6")
        monitor.start()
        monitor.stop()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_report.json")
            monitor.save_report(output_path)
            
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                report = json.load(f)
            
            assert report['run_id'] == "test_run_6"
            assert report['duration_seconds'] > 0


class TestMonitorAgentRunContextManager:
    """Tests for the monitor_agent_run context manager."""

    def test_context_manager_execution(self):
        """Test that the context manager yields the monitor and saves the report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "context_report.json")
            run_id = "context_test_1"
            
            with monitor_agent_run(run_id, output_path, sample_interval=0.2) as monitor:
                time.sleep(0.5)
                assert monitor is not None
            
            # Check file was created
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                report = json.load(f)
            
            assert report['run_id'] == run_id
            assert report['duration_seconds'] >= 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
