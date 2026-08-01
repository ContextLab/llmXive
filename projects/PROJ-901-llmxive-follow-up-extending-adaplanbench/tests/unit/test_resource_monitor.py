"""
Unit tests for the resource monitor wrapper in code/main.py.
Verifies schema and exception raising behavior.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from main import ResourceMonitor, ResourceLimitExceeded
from config import get_paths


class TestResourceMonitorSchema:
    """Test that ResourceMonitor produces the correct JSON schema."""

    def test_snapshot_schema_structure(self):
        """Verify the snapshot dictionary has all required keys."""
        monitor = ResourceMonitor("test_task_1")
        monitor._log_snapshot(cpu=50.0, ram=2.5)
        
        assert len(monitor.snapshots) == 1
        snapshot = monitor.snapshots[0]
        
        # Check required keys
        assert "timestamp" in snapshot
        assert "task_id" in snapshot
        assert "cpu_percent" in snapshot
        assert "ram_gb" in snapshot
        assert "threshold_exceeded" in snapshot
        assert "exceeded_limit" in snapshot
        assert "snapshot_values" in snapshot
        
        # Check types
        assert isinstance(snapshot["timestamp"], str)
        assert snapshot["task_id"] == "test_task_1"
        assert isinstance(snapshot["cpu_percent"], float)
        assert isinstance(snapshot["ram_gb"], float)
        assert isinstance(snapshot["threshold_exceeded"], bool)
        assert snapshot["threshold_exceeded"] is False
        assert snapshot["exceeded_limit"] is None
        assert isinstance(snapshot["snapshot_values"], dict)
        assert "cpu" in snapshot["snapshot_values"]
        assert "ram" in snapshot["snapshot_values"]

    def test_schema_values_correct(self):
        """Verify values are correctly populated."""
        monitor = ResourceMonitor("test_task_2")
        monitor._log_snapshot(cpu=75.5, ram=4.2)
        
        snapshot = monitor.snapshots[0]
        assert snapshot["cpu_percent"] == 75.5
        assert snapshot["ram_gb"] == 4.2
        assert snapshot["snapshot_values"]["cpu"] == 75.5
        assert snapshot["snapshot_values"]["ram"] == 4.2


class TestResourceMonitorThresholds:
    """Test threshold detection and exception raising."""

    def test_cpu_threshold_exceeded(self):
        """Test that CPU > 90% triggers exception."""
        # Create a temporary file for logs
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name

        try:
            monitor = ResourceMonitor("test_cpu_exceed", log_path=Path(temp_path))
            # Simulate CPU > 90%
            monitor._log_snapshot(cpu=95.0, ram=2.0)
            
            assert monitor.exceeded is True
            assert monitor.exceeded_limit == "CPU"
            assert monitor.trigger_values is not None
            assert monitor.trigger_values["cpu"] == 95.0
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_ram_threshold_exceeded(self):
        """Test that RAM > 6.5GB triggers exception."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name

        try:
            monitor = ResourceMonitor("test_ram_exceed", log_path=Path(temp_path))
            # Simulate RAM > 6.5GB
            monitor._log_snapshot(cpu=50.0, ram=7.0)
            
            assert monitor.exceeded is True
            assert monitor.exceeded_limit == "RAM"
            assert monitor.trigger_values is not None
            assert monitor.trigger_values["ram"] == 7.0
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_exception_raised_on_exit(self):
        """Test that ResourceLimitExceeded is raised on context exit."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name

        try:
            with patch.object(ResourceMonitor, '_get_current_usage', return_value=(95.0, 2.0)):
                with pytest.raises(ResourceLimitExceeded) as exc_info:
                    with ResourceMonitor("test_exception", log_path=Path(temp_path)) as monitor:
                        # Do nothing, just exit context
                        pass
                
                assert "CPU" in str(exc_info.value)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_no_exception_below_threshold(self):
        """Test that no exception is raised when below thresholds."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name

        try:
            with patch.object(ResourceMonitor, '_get_current_usage', return_value=(50.0, 2.0)):
                with ResourceMonitor("test_safe", log_path=Path(temp_path)) as monitor:
                    pass  # Should not raise
                
                assert monitor.exceeded is False
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestResourceMonitorLogging:
    """Test that logs are correctly written to disk."""

    def test_logs_written_to_file(self):
        """Verify logs are written to the specified path."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name

        try:
            with patch.object(ResourceMonitor, '_get_current_usage', return_value=(50.0, 2.0)):
                with ResourceMonitor("test_log", log_path=Path(temp_path)) as monitor:
                    pass
            
            # Verify file exists and contains valid JSON
            assert os.path.exists(temp_path)
            with open(temp_path, 'r') as f:
                logs = json.load(f)
            
            assert isinstance(logs, list)
            assert len(logs) >= 1
            assert logs[0]["task_id"] == "test_log"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_logs_append_existing(self):
        """Verify new logs are appended to existing logs."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            f.write(json.dumps([{"timestamp": "old", "task_id": "old_task"}]))
            temp_path = f.name

        try:
            with patch.object(ResourceMonitor, '_get_current_usage', return_value=(50.0, 2.0)):
                with ResourceMonitor("test_append", log_path=Path(temp_path)) as monitor:
                    pass
            
            with open(temp_path, 'r') as f:
                logs = json.load(f)
            
            assert len(logs) == 2
            assert logs[0]["task_id"] == "old_task"
            assert logs[1]["task_id"] == "test_append"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
