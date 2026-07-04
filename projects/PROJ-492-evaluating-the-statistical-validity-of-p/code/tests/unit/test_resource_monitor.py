"""
Unit tests for resource_monitor.py
"""
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from code.src.utils.resource_monitor import (
    ResourceMonitor,
    start_monitoring,
    stop_monitoring,
    write_resource_log,
    get_memory_usage_gb,
    get_cpu_cores,
    ERR_RESOURCE_LIMIT,
    MAX_MEMORY_GB,
    MAX_CPU_CORES,
)
from code.src.utils.logger import get_default_logger


class TestResourceMonitor:
    """Tests for ResourceMonitor class."""

    def test_monitor_initialization(self):
        """Test that ResourceMonitor initializes correctly."""
        monitor = ResourceMonitor()
        assert monitor._peak_memory_mb == 0.0
        assert monitor._peak_cpu_percent == 0.0
        assert not monitor._monitoring
        assert monitor._process is not None  # Should have process if psutil available

    def test_start_and_stop(self):
        """Test starting and stopping the monitor."""
        monitor = ResourceMonitor()
        monitor.start(interval=0.1)
        assert monitor._monitoring
        assert monitor._thread is not None
        assert monitor._start_time is not None

        time.sleep(0.2)  # Let it run briefly
        monitor.stop()
        assert not monitor._monitoring

    def test_get_resource_summary(self):
        """Test that get_resource_summary returns expected keys."""
        monitor = ResourceMonitor()
        monitor.start(interval=0.1)
        time.sleep(0.2)
        summary = monitor.get_resource_summary()

        assert "peak_memory_gb" in summary
        assert "peak_cpu_percent" in summary
        assert "elapsed_seconds" in summary
        assert "max_memory_limit_gb" in summary
        assert "max_cpu_cores_limit" in summary
        assert "timestamp" in summary
        assert summary["max_memory_limit_gb"] == MAX_MEMORY_GB
        assert summary["max_cpu_cores_limit"] == MAX_CPU_CORES

        monitor.stop()

    def test_write_log(self):
        """Test writing resource log to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "resource_log.json"
            monitor = ResourceMonitor()
            monitor.start(interval=0.1)
            time.sleep(0.2)
            monitor.write_log(output_path)
            monitor.stop()

            assert output_path.exists()
            with open(output_path, 'r') as f:
                log_data = json.load(f)

            assert "peak_memory_gb" in log_data
            assert "peak_cpu_percent" in log_data
            assert log_data["status"] == "completed"

    def test_memory_limit_check(self):
        """Test that memory limit check works (mocked)."""
        with patch('code.src.utils.resource_monitor.psutil') as mock_psutil:
            mock_process = MagicMock()
            # Mock memory to exceed limit (3 GB)
            mock_process.memory_info.return_value = MagicMock(rss=3 * 1024 * 1024 * 1024)
            mock_psutil.Process.return_value = mock_process
            mock_psutil.cpu_count.return_value = 4

            monitor = ResourceMonitor()
            monitor._process = mock_process

            # This should trigger an abort
            with pytest.raises(SystemExit) as exc_info:
                monitor._check_limits()

            assert exc_info.value.code == 1

    def test_cpu_limit_check(self):
        """Test that CPU limit check works (mocked)."""
        with patch('code.src.utils.resource_monitor.psutil') as mock_psutil:
            mock_process = MagicMock()
            mock_process.memory_info.return_value = MagicMock(rss=100 * 1024 * 1024)  # 100 MB
            mock_process.cpu_percent.return_value = 300  # 300% = 3 cores
            mock_psutil.Process.return_value = mock_process
            mock_psutil.cpu_count.return_value = 4

            monitor = ResourceMonitor()
            monitor._process = mock_process
            monitor._peak_cpu_percent = 300.0

            # This should trigger an abort
            with pytest.raises(SystemExit) as exc_info:
                monitor._check_limits()

            assert exc_info.value.code == 1

    def test_limits_not_exceeded(self):
        """Test that no abort occurs when limits are not exceeded."""
        with patch('code.src.utils.resource_monitor.psutil') as mock_psutil:
            mock_process = MagicMock()
            mock_process.memory_info.return_value = MagicMock(rss=500 * 1024 * 1024)  # 500 MB
            mock_process.cpu_percent.return_value = 100  # 100% = 1 core
            mock_psutil.Process.return_value = mock_process
            mock_psutil.cpu_count.return_value = 4

            monitor = ResourceMonitor()
            monitor._process = mock_process
            monitor._peak_memory_mb = 500.0
            monitor._peak_cpu_percent = 100.0

            # Should not raise
            try:
                monitor._check_limits()
            except SystemExit:
                pytest.fail("_check_limits() should not raise when limits not exceeded")


class TestGlobalFunctions:
    """Tests for global convenience functions."""

    def test_start_and_stop_monitoring(self):
        """Test global start/stop monitoring functions."""
        monitor = start_monitoring(interval=0.1)
        assert monitor is not None
        assert monitor._monitoring

        time.sleep(0.2)
        stop_monitoring()
        assert not monitor._monitoring

    def test_write_resource_log(self):
        """Test global write_resource_log function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_log.json"
            
            # Start a monitor first
            monitor = start_monitoring(interval=0.1)
            time.sleep(0.2)
            
            write_resource_log(output_path)
            stop_monitoring()

            assert output_path.exists()
            with open(output_path, 'r') as f:
                log_data = json.load(f)
            
            assert "peak_memory_gb" in log_data

    def test_get_memory_usage_gb(self):
        """Test get_memory_usage_gb function."""
        try:
            import psutil
            usage = get_memory_usage_gb()
            assert usage >= 0.0
        except ImportError:
            # If psutil not available, should return 0.0
            usage = get_memory_usage_gb()
            assert usage == 0.0

    def test_get_cpu_cores(self):
        """Test get_cpu_cores function."""
        try:
            import psutil
            cores = get_cpu_cores()
            assert cores >= 0.0
        except ImportError:
            # If psutil not available, should return 0.0
            cores = get_cpu_cores()
            assert cores == 0.0

    def test_write_resource_log_without_monitor(self):
        """Test write_resource_log when no monitor is running."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_log.json"
            
            # Ensure no monitor is running
            stop_monitoring()
            
            write_resource_log(output_path)

            assert output_path.exists()
            with open(output_path, 'r') as f:
                log_data = json.load(f)
            
            assert log_data["status"] == "not_started"
            assert log_data["peak_memory_gb"] == 0.0


class TestErrorHandling:
    """Tests for error handling scenarios."""

    def test_monitor_without_psutil(self):
        """Test monitor behavior when psutil is not available."""
        with patch('code.src.utils.resource_monitor.psutil', None):
            monitor = ResourceMonitor()
            assert monitor._process is None

            # Should not crash when starting
            monitor.start(interval=0.1)
            # Should have logged a warning
            monitor.stop()

    def test_abort_error_code(self):
        """Test that abort uses correct error code."""
        assert ERR_RESOURCE_LIMIT == "ERR-301"