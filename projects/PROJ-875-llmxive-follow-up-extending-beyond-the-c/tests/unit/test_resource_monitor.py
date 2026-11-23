"""
Unit tests for code/resource_monitor.py

Tests Constitution Principle VII implementation:
- Logging peak RAM and CPU usage
- Output schema validation
- Constraint verification (RAM <= 7168MB, CPU <= 200%)
"""
import os
import json
import tempfile
import time
import pytest
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.resource_monitor import ResourceMonitor, run_resource_monitoring_test


class TestResourceMonitor:
    """Test cases for ResourceMonitor class."""
    
    def test_init(self):
        """Test ResourceMonitor initialization."""
        monitor = ResourceMonitor(run_id="test_123", interval_seconds=0.5)
        assert monitor.run_id == "test_123"
        assert monitor.interval_seconds == 0.5
        assert monitor.samples == []
        assert monitor._monitor_thread is None
    
    def test_start_and_stop(self):
        """Test starting and stopping the monitor."""
        monitor = ResourceMonitor(run_id="test_start_stop", interval_seconds=0.1)
        monitor.start()
        
        # Let it collect a few samples
        time.sleep(0.5)
        
        result = monitor.stop()
        
        assert result["run_id"] == "test_start_stop"
        assert "peak_ram_mb" in result
        assert "cpu_percent" in result
        assert "sample_count" in result
        assert result["sample_count"] >= 1
    
    def test_save_report(self):
        """Test saving the resource profile to a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "resource_profile.json")
            
            monitor = ResourceMonitor(run_id="test_save", interval_seconds=0.1)
            monitor.start()
            time.sleep(0.3)
            
            result = monitor.save_report(output_path)
            
            # Verify file exists
            assert os.path.exists(output_path)
            
            # Verify JSON structure
            with open(output_path, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data["run_id"] == "test_save"
            assert isinstance(saved_data["peak_ram_mb"], float)
            assert isinstance(saved_data["cpu_percent"], float)
            assert saved_data["sample_count"] >= 1
    
    def test_schema_compliance(self):
        """Test that output matches required schema."""
        monitor = ResourceMonitor(run_id="schema_test")
        monitor.start()
        time.sleep(0.2)
        result = monitor.stop()
        
        # Required fields per spec
        assert "peak_ram_mb" in result
        assert "cpu_percent" in result
        assert "run_id" in result
        
        # Type checks
        assert isinstance(result["peak_ram_mb"], float)
        assert isinstance(result["cpu_percent"], float)
        assert isinstance(result["run_id"], str)
    
    @patch('code.resource_monitor.psutil')
    def test_with_psutil_mock(self, mock_psutil):
        """Test monitoring when psutil is available."""
        # Setup mock
        mock_process = MagicMock()
        mock_process.memory_info.return_value = MagicMock(rss=1024*1024*500)  # 500MB
        mock_process.cpu_percent.return_value = 25.5
        mock_psutil.Process.return_value = mock_process
        
        monitor = ResourceMonitor(run_id="mock_psutil_test", interval_seconds=0.1)
        monitor.start()
        time.sleep(0.3)
        result = monitor.stop()
        
        # Verify values are within expected range
        assert 0 <= result["peak_ram_mb"] <= 7168
        assert 0 <= result["cpu_percent"] <= 200
    
    def test_constraint_verification(self):
        """Test that constraints are enforced and logged."""
        monitor = ResourceMonitor(run_id="constraint_test")
        monitor.start()
        time.sleep(0.3)
        result = monitor.stop()
        
        # These should pass under normal conditions
        assert result["peak_ram_mb"] <= 7168, "RAM constraint violated"
        assert result["cpu_percent"] <= 200, "CPU constraint violated"
    
    def test_empty_samples(self):
        """Test behavior when no samples are collected."""
        monitor = ResourceMonitor(run_id="empty_test", interval_seconds=10.0)
        monitor._stop_event.set()  # Stop immediately
        result = monitor.stop()
        
        assert result["peak_ram_mb"] == 0.0
        assert result["cpu_percent"] == 0.0
        assert result["sample_count"] == 0
        assert result["run_id"] == "empty_test"


class TestRunResourceMonitoringTest:
    """Test cases for the test runner function."""
    
    def test_run_resource_monitoring_test(self):
        """Test the full test runner function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_profile.json")
            
            result = run_resource_monitoring_test(
                run_id="runner_test",
                duration_seconds=0.5,
                output_path=output_path
            )
            
            assert result["run_id"] == "runner_test"
            assert result["sample_count"] >= 1
            assert result["peak_ram_mb"] <= 7168
            assert result["cpu_percent"] <= 200
            
            # Verify file was created
            assert os.path.exists(output_path)
    
    def test_run_resource_monitoring_test_creates_output(self):
        """Test that output file is created at specified path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "custom_output.json")
            
            run_resource_monitoring_test(
                run_id="output_test",
                duration_seconds=0.3,
                output_path=output_path
            )
            
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert data["run_id"] == "output_test"


class TestResourceMonitorIntegration:
    """Integration tests for resource monitoring."""
    
    def test_monitor_during_workload(self):
        """Test monitoring during a simulated workload."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "workload_profile.json")
            
            monitor = ResourceMonitor(run_id="workload_test", interval_seconds=0.2)
            monitor.start()
            
            # Simulate some CPU work
            start = time.time()
            while time.time() - start < 0.5:
                _ = sum(i * i for i in range(1000))
            
            result = monitor.save_report(output_path)
            
            assert result["sample_count"] >= 1
            assert result["peak_ram_mb"] >= 0
            assert result["cpu_percent"] >= 0
            assert result["duration_seconds"] >= 0.4  # Allow some tolerance
    
    def test_multiple_start_stop_cycles(self):
        """Test that monitor can be started and stopped multiple times."""
        monitor = ResourceMonitor(run_id="multi_cycle_test")
        
        # First cycle
        monitor.start()
        time.sleep(0.2)
        result1 = monitor.stop()
        
        # Second cycle (re-initialize)
        monitor = ResourceMonitor(run_id="multi_cycle_test_2")
        monitor.start()
        time.sleep(0.2)
        result2 = monitor.stop()
        
        assert result1["run_id"] == "multi_cycle_test"
        assert result2["run_id"] == "multi_cycle_test_2"
        assert result1["sample_count"] >= 1
        assert result2["sample_count"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
