"""
Unit tests for memory monitoring functionality.
"""
import os
import sys
import json
import time
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.memory_monitor import MemoryMonitor, MemorySnapshot, verify_memory_limits


class TestMemoryMonitor:
    """Tests for the MemoryMonitor class."""

    def test_init_default(self):
        """Test initialization with default parameters."""
        monitor = MemoryMonitor()
        assert monitor is not None
        assert monitor.samples == []
        assert monitor.peak_memory_mb == 0.0
        assert monitor.monitoring is False
        assert monitor.check_interval > 0
        assert monitor.max_memory_limit_mb > 0

    def test_init_custom_limit(self):
        """Test initialization with custom memory limit."""
        monitor = MemoryMonitor()
        monitor.max_memory_limit_mb = 8000.0
        assert monitor.max_memory_limit_mb == 8000.0

    def test_start_and_stop(self):
        """Test starting and stopping the monitor."""
        monitor = MemoryMonitor()
        monitor.start()
        assert monitor.monitoring is True
        assert len(monitor.samples) > 0

        time.sleep(0.5)  # Allow some samples to be collected
        summary = monitor.stop()

        assert monitor.monitoring is False
        assert summary["status"] in ["success", "exceeded"]
        assert "peak_memory_mb" in summary

    def test_take_snapshot(self):
        """Test taking a single snapshot."""
        monitor = MemoryMonitor()
        monitor.start()

        snapshot = monitor._take_snapshot()

        assert isinstance(snapshot, MemorySnapshot)
        assert snapshot.timestamp is not None
        assert snapshot.process_memory_mb >= 0
        assert snapshot.system_memory_percent >= 0

        monitor.stop()

    def test_get_current_usage(self):
        """Test getting current memory usage."""
        monitor = MemoryMonitor()
        usage = monitor.get_current_usage()

        assert "process_memory_mb" in usage
        assert "system_memory_percent" in usage
        assert "peak_memory_mb" in usage
        assert usage["process_memory_mb"] >= 0

    def test_check_limit(self):
        """Test memory limit checking."""
        monitor = MemoryMonitor()
        monitor.max_memory_limit_mb = 100000.0  # Set very high limit

        is_within = monitor.check_limit()
        assert is_within is True

        # Test with very low limit
        monitor.max_memory_limit_mb = 0.001  # Extremely low
        is_within = monitor.check_limit()
        assert is_within is False

    def test_get_summary_no_samples(self):
        """Test getting summary with no samples."""
        monitor = MemoryMonitor()
        summary = monitor.get_summary()

        assert summary["status"] == "no_data"
        assert "message" in summary

    def test_get_summary_with_samples(self):
        """Test getting summary with samples."""
        monitor = MemoryMonitor()
        monitor.start()

        # Collect some samples
        for _ in range(5):
            monitor._take_snapshot()
            time.sleep(0.1)

        summary = monitor.stop()

        assert summary["status"] in ["success", "exceeded"]
        assert summary["sample_count"] >= 5
        assert "statistics" in summary
        assert "process_memory_mb" in summary["statistics"]
        assert "system_memory_percent" in summary["statistics"]

    def test_save_report(self, tmp_path):
        """Test saving report to file."""
        monitor = MemoryMonitor()
        monitor.project_root = tmp_path
        monitor.log_dir = tmp_path / "data" / "logs"
        monitor.log_dir.mkdir(parents=True, exist_ok=True)

        monitor.start()
        monitor._take_snapshot()
        summary = monitor.stop()

        report_path = monitor.log_dir / "memory_monitor_report.json"
        assert report_path.exists()

        with open(report_path) as f:
            saved_data = json.load(f)

        assert saved_data["status"] == summary["status"]
        assert saved_data["peak_memory_mb"] == summary["peak_memory_mb"]

    def test_peak_memory_tracking(self):
        """Test that peak memory is correctly tracked."""
        monitor = MemoryMonitor()
        monitor.start()

        # Take initial snapshot
        snapshot1 = monitor._take_snapshot()
        initial_peak = snapshot1.process_memory_mb

        # Simulate higher memory usage
        data = [i * 1000 for i in range(100000)]
        snapshot2 = monitor._take_snapshot()
        del data

        assert monitor.peak_memory_mb >= initial_peak
        assert snapshot2.peak_memory_mb >= initial_peak

        monitor.stop()


class TestVerifyMemoryLimits:
    """Tests for the verify_memory_limits function."""

    def test_verify_memory_limits_basic(self):
        """Test basic memory limit verification."""
        result = verify_memory_limits(check_interval=0.5)

        assert "status" in result
        assert "peak_memory_mb" in result
        assert "within_limits" in result
        assert result["sample_count"] >= 1

    def test_verify_memory_limits_custom_params(self):
        """Test with custom parameters."""
        result = verify_memory_limits(max_memory_mb=100000, check_interval=0.2)

        assert result["max_memory_limit_mb"] == 100000
        assert result["within_limits"] is True


class TestMemorySnapshot:
    """Tests for the MemorySnapshot dataclass."""

    def test_snapshot_creation(self):
        """Test creating a snapshot."""
        snapshot = MemorySnapshot(
            timestamp="2024-01-01T00:00:00",
            process_memory_mb=500.0,
            system_memory_percent=45.0,
            system_memory_available_mb=4000.0
        )

        assert snapshot.timestamp == "2024-01-01T00:00:00"
        assert snapshot.process_memory_mb == 500.0
        assert snapshot.system_memory_percent == 45.0
        assert snapshot.system_memory_available_mb == 4000.0

    def test_snapshot_as_dict(self):
        """Test converting snapshot to dictionary."""
        from dataclasses import asdict

        snapshot = MemorySnapshot(
            timestamp="2024-01-01T00:00:00",
            process_memory_mb=500.0,
            system_memory_percent=45.0,
            system_memory_available_mb=4000.0
        )

        snapshot_dict = asdict(snapshot)
        assert isinstance(snapshot_dict, dict)
        assert "timestamp" in snapshot_dict
        assert "process_memory_mb" in snapshot_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])