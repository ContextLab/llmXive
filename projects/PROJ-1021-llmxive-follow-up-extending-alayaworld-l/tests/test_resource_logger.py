"""
Tests for the resource_logger module.
"""
import json
import os
import time
import tempfile
from pathlib import Path

import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils.resource_logger import ResourceMonitor, RAM_LIMIT_MB, TIME_LIMIT_SECONDS


def test_monitor_initialization():
    """Test that the monitor initializes correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monitor = ResourceMonitor("test_seq_1", log_dir=tmpdir)
        assert monitor.sequence_id == "test_seq_1"
        assert monitor.log_dir == Path(tmpdir)
        assert not monitor.is_monitoring
        assert monitor.start_time is None


def test_start_stop_cycle():
    """Test starting and stopping the monitor."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monitor = ResourceMonitor("test_seq_2", log_dir=tmpdir)
        monitor.start()
        assert monitor.is_monitoring
        assert monitor.start_time is not None

        # Do nothing, just stop
        summary = monitor.stop()

        assert not monitor.is_monitoring
        assert summary["status"] == "completed"
        assert summary["peak_ram_mb"] >= 0
        assert summary["wall_clock_seconds"] >= 0
        assert Path(summary["log_file"]).exists()


def test_log_file_creation():
    """Test that the log file is created and contains valid JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monitor = ResourceMonitor("test_seq_3", log_dir=tmpdir)
        monitor.start()
        monitor.record_step({"metric": 123})
        time.sleep(0.1)
        monitor.stop()

        log_path = Path(tmpdir) / f"realtime_seq_test_seq_3_*.json"
        # Find the file
        files = list(Path(tmpdir).glob("realtime_seq_test_seq_3_*.json"))
        assert len(files) == 1

        with open(files[0], "r") as f:
            data = json.load(f)

        assert "samples" in data
        assert len(data["samples"]) >= 1
        assert data["samples"][0]["step_data"]["metric"] == 123


def test_ram_sampling():
    """Test that RAM is sampled and peak is recorded."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monitor = ResourceMonitor("test_seq_4", log_dir=tmpdir)
        monitor.start()

        # Force some memory usage to ensure a sample > 0
        dummy_list = [0] * 1000000
        monitor.record_step()
        del dummy_list

        monitor.stop()

        assert monitor.peak_ram_mb > 0


def test_time_limit_exceeded():
    """Test that a timeout error is raised if time limit is exceeded."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Temporarily lower the limit for testing
        original_limit = TIME_LIMIT_SECONDS
        import utils.resource_logger
        utils.resource_logger.TIME_LIMIT_SECONDS = 0.1

        try:
            monitor = ResourceMonitor("test_seq_5", log_dir=tmpdir)
            monitor.start()
            time.sleep(0.2)  # Sleep longer than the limit

            # This should raise TimeoutError on the next step check or stop
            with pytest.raises(TimeoutError):
                monitor.record_step()
        finally:
            utils.resource_logger.TIME_LIMIT_SECONDS = original_limit


def test_ram_limit_exceeded():
    """Test that a memory error is raised if RAM limit is exceeded."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Temporarily lower the limit for testing
        original_limit = RAM_LIMIT_MB
        import utils.resource_logger
        # Set limit to a very low value (e.g., 1 MB) to trigger easily
        utils.resource_logger.RAM_LIMIT_MB = 1.0

        try:
            monitor = ResourceMonitor("test_seq_6", log_dir=tmpdir)
            monitor.start()

            # Allocate a chunk of memory to exceed 1MB
            # 10MB should be enough
            dummy_list = [0] * (10 * 1024 * 1024)

            with pytest.raises(MemoryError):
                monitor.record_step()
        finally:
            utils.resource_logger.RAM_LIMIT_MB = original_limit
            del dummy_list