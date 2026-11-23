import os
import sys
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import psutil

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import ResourceLimitExceeded, get_paths, get_resource_limits
from main import ResourceMonitor, ResourceMetrics, resource_monitor_context

@pytest.fixture
def mock_paths(tmp_path):
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    with patch('config.get_paths') as mock_get_paths:
        mock_paths = MagicMock()
        mock_paths.PROCESSED = processed_dir
        mock_get_paths.return_value = mock_paths
        yield mock_paths

@pytest.fixture
def mock_limits():
    limits = MagicMock()
    limits.MAX_CPU_PERCENT = 90.0
    limits.MAX_RAM_GB = 6.5
    with patch('config.get_resource_limits', return_value=limits):
        yield limits

@pytest.fixture
def monitor(mock_paths, mock_limits):
    return ResourceMonitor(task_id="TEST_TASK_001")

def test_resource_metrics_creation():
    metrics = ResourceMetrics(cpu_percent=50.0, ram_gb=2.0)
    assert metrics.cpu_percent == 50.0
    assert metrics.ram_gb == 2.0

def test_monitor_initialization(monitor):
    assert monitor.task_id == "TEST_TASK_001"
    # Log file might not exist yet if not created by __init__ in the new version
    # but the fixture ensures the path is valid.
    # In the implementation, we create the file if it doesn't exist.
    assert monitor.log_file.parent.exists()

def test_get_snapshot(monitor):
    with patch.object(monitor, 'process') as mock_process:
        mock_process.cpu_percent.return_value = 45.5
        mock_process.memory_info.return_value = MagicMock(rss=1024**3 * 2.0)
        metrics = monitor._get_snapshot()
        assert metrics.cpu_percent == 45.5
        assert metrics.ram_gb == 2.0

def test_check_limits_within(monitor, mock_limits):
    metrics = ResourceMetrics(cpu_percent=50.0, ram_gb=2.0)
    assert monitor._check_limits(metrics) is None

def test_check_limits_cpu_exceeded(monitor, mock_limits):
    metrics = ResourceMetrics(cpu_percent=95.0, ram_gb=2.0)
    assert monitor._check_limits(metrics) == "CPU"

def test_check_limits_ram_exceeded(monitor, mock_limits):
    metrics = ResourceMetrics(cpu_percent=50.0, ram_gb=7.0)
    assert monitor._check_limits(metrics) == "RAM"

def test_log_entry_creation(monitor, mock_paths, mock_limits):
    metrics = ResourceMetrics(cpu_percent=50.0, ram_gb=2.0)
    monitor._log_entry(metrics, False, None)
    
    assert monitor.log_file.exists()
    with open(monitor.log_file, 'r') as f:
        logs = json.load(f)
    
    assert len(logs) == 1
    entry = logs[0]
    assert entry["task_id"] == "TEST_TASK_001"
    assert entry["cpu_percent"] == 50.0
    assert entry["ram_gb"] == 2.0
    assert entry["threshold_exceeded"] is False
    assert entry["exceeded_limit"] is None
    assert "snapshot_values" in entry
    assert entry["snapshot_values"]["cpu"] == 50.0
    assert entry["snapshot_values"]["ram"] == 2.0
    assert "timestamp" in entry

def test_wrap_task_success(monitor, mock_paths, mock_limits):
    def success_func():
        return "success"
    
    result = monitor.wrap_task(success_func)
    assert result == "success"
    
    # Check log file
    with open(monitor.log_file, 'r') as f:
        logs = json.load(f)
    assert len(logs) >= 1
    assert logs[-1]["threshold_exceeded"] is False

def test_wrap_task_resource_exceeded(monitor, mock_paths, mock_limits):
    def failing_func():
        return "should not reach"
    
    # Mock the snapshot to return exceeded values
    with patch.object(monitor, '_get_snapshot') as mock_snapshot:
        mock_snapshot.return_value = ResourceMetrics(cpu_percent=95.0, ram_gb=2.0)
        
        with pytest.raises(ResourceLimitExceeded) as exc_info:
            monitor.wrap_task(failing_func)
        
        assert "CPU" in str(exc_info.value)
        
        # Verify log was written before raising
        with open(monitor.log_file, 'r') as f:
            logs = json.load(f)
        assert len(logs) >= 1
        assert logs[-1]["threshold_exceeded"] is True
        assert logs[-1]["exceeded_limit"] == "CPU"

def test_wrap_task_exception_logging(monitor, mock_paths, mock_limits):
    def error_func():
        raise ValueError("Test error")
    
    with pytest.raises(ValueError):
        monitor.wrap_task(error_func)
    
    # Check log file for failure state
    with open(monitor.log_file, 'r') as f:
        logs = json.load(f)
    assert len(logs) >= 1
    # The last entry should reflect the state at failure
    assert logs[-1]["task_id"] == "TEST_TASK_001"

def test_resource_monitor_context_factory():
    with patch('config.get_paths'), patch('config.get_resource_limits'):
        ctx = resource_monitor_context("CTX_TASK")
        assert isinstance(ctx, ResourceMonitor)
        assert ctx.task_id == "CTX_TASK"