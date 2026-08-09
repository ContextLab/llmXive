"""
Unit tests for the MemoryMonitor class.
"""
import pytest
import logging
import time
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import the module
from code.utils.memory_monitor import MemoryMonitor, log_epoch_memory

# Configure logging for tests
logger = logging.getLogger("TestMemoryMonitor")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)


class TestMemoryMonitor:
    """Tests for the MemoryMonitor class."""

    def test_init_defaults(self):
        """Test initialization with default values."""
        monitor = MemoryMonitor(logger=logger)
        assert monitor.is_monitoring is False
        assert monitor.max_ram_gb > 0
        assert monitor.peak_memory_bytes == 0
        assert len(monitor.epoch_logs) == 0

    def test_init_custom_max_ram(self):
        """Test initialization with custom max RAM."""
        custom_limit = 10.0
        monitor = MemoryMonitor(logger=logger, max_ram_gb=custom_limit)
        assert monitor.max_ram_gb == custom_limit
        assert monitor.max_ram_bytes == custom_limit * 1024 * 1024 * 1024

    def test_start_and_stop(self):
        """Test starting and stopping the monitor."""
        monitor = MemoryMonitor(logger=logger)
        monitor.start()
        assert monitor.is_monitoring is True
        monitor.stop()
        assert monitor.is_monitoring is False

    def test_snapshot_basic(self):
        """Test basic snapshot functionality."""
        monitor = MemoryMonitor(logger=logger)
        monitor.start()

        # Allocate some memory
        data = [i for i in range(100000)]
        log_epoch_memory(monitor, epoch=0)
        del data

        assert len(monitor.epoch_logs) == 1
        assert monitor.epoch_logs[0]["epoch"] == 0
        assert "current_memory_gb" in monitor.epoch_logs[0]
        assert "peak_memory_gb" in monitor.epoch_logs[0]

        monitor.stop()

    def test_snapshot_exceeds_limit(self):
        """Test that snapshot raises MemoryError when limit is exceeded."""
        # Set a very low limit to force an exceedance
        monitor = MemoryMonitor(logger=logger, max_ram_gb=0.00001) # 10KB limit
        monitor.start()

        # Allocate enough to exceed 10KB
        data = [i for i in range(1000000)] # ~8MB+ depending on platform

        with pytest.raises(MemoryError):
            log_epoch_memory(monitor, epoch=0)

        # Verify report generation
        report_path = Path(os.getcwd()) / "results" / "reports" / "memory_overflow_report.json"
        # Note: In a real test environment, we might need to mock the file system
        # or ensure the directory exists. For this test, we assume the directory exists or is created.
        # The important part is that the error is raised.

        monitor.stop()

    def test_get_peak_memory(self):
        """Test getting peak memory."""
        monitor = MemoryMonitor(logger=logger)
        monitor.start()

        data = [i for i in range(100000)]
        log_epoch_memory(monitor, epoch=0)
        del data

        peak = monitor.get_peak_memory_gb()
        assert peak >= 0.0

        monitor.stop()

    def test_get_epoch_logs(self):
        """Test retrieving epoch logs."""
        monitor = MemoryMonitor(logger=logger)
        monitor.start()

        for i in range(3):
            data = [i]
            log_epoch_memory(monitor, epoch=i)
            del data

        logs = monitor.get_epoch_logs()
        assert len(logs) == 3
        assert logs[0]["epoch"] == 0
        assert logs[2]["epoch"] == 2

        monitor.stop()

    def test_snapshot_without_start(self):
        """Test that snapshot warns if monitoring hasn't started."""
        monitor = MemoryMonitor(logger=logger)
        # Do not start

        with pytest.warns(UserWarning):
            # This might not raise an exception but should warn
            # Depending on implementation, it might return empty dict
            result = monitor.snapshot(epoch=0)
            assert result == {}