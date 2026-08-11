import os
import sys
import json
import time
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils import ResourceMonitor, ResourceUsage

class TestResourceMonitor:
    """Unit tests for ResourceMonitor class."""

    def test_init_creates_processed_dir(self, tmp_path):
        """Test that __init__ creates the data/processed directory."""
        # Temporarily change the processed_dir path for testing
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            monitor = ResourceMonitor()
            assert monitor.processed_dir.exists()
            assert monitor.processed_dir.is_dir()
        finally:
            os.chdir(original_cwd)

    def test_start_and_stop_no_args(self):
        """Test that start() and stop() take no arguments."""
        monitor = ResourceMonitor()
        # These should not raise TypeError
        monitor.start()
        monitor.stop()
        assert len(monitor.snapshots) == 2

    def test_finalize_writes_json(self, tmp_path):
        """Test that finalize() writes resource_profile.json."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            monitor = ResourceMonitor()
            monitor.start()
            # Simulate some time passing
            time.sleep(0.01)
            monitor.stop()
            monitor.finalize()

            output_path = Path("data/processed/resource_profile.json")
            assert output_path.exists()

            with open(output_path, 'r') as f:
                profile = json.load(f)

            assert "peak_ram_gb" in profile
            assert "total_runtime_hours" in profile
            assert isinstance(profile["peak_ram_gb"], float)
            assert isinstance(profile["total_runtime_hours"], float)
        finally:
            os.chdir(original_cwd)

    def test_peak_ram_and_runtime_positive_with_mock(self, tmp_path):
        """
        Test that peak_ram_gb > 0 and total_runtime_hours > 0 when
        simulated memory usage is provided via psutil mock.
        """
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            monitor = ResourceMonitor()

            # Mock psutil to return a non-zero memory value
            mock_process = MagicMock()
            mock_process.memory_info.return_value.rss = 2 * 1024 * 1024 * 1024  # 2 GB in bytes

            with patch('psutil.Process', return_value=mock_process):
                monitor.start()
                time.sleep(0.05)  # Ensure some time passes
                monitor.stop()
                monitor.finalize()

            output_path = Path("data/processed/resource_profile.json")
            with open(output_path, 'r') as f:
                profile = json.load(f)

            # Assertions per task requirements
            assert profile["peak_ram_gb"] > 0, f"Expected peak_ram_gb > 0, got {profile['peak_ram_gb']}"
            assert profile["total_runtime_hours"] > 0, f"Expected total_runtime_hours > 0, got {profile['total_runtime_hours']}"

        finally:
            os.chdir(original_cwd)

    def test_snapshots_recorded_correctly(self):
        """Test that snapshots are recorded with correct subject_id and ram_gb."""
        monitor = ResourceMonitor()
        monitor.set_subject("sub-001")
        monitor.start()
        monitor.stop()

        assert len(monitor.snapshots) == 2
        for snapshot in monitor.snapshots:
            assert isinstance(snapshot, ResourceUsage)
            assert snapshot.subject_id == "sub-001"
            assert isinstance(snapshot.ram_gb, float)
            assert isinstance(snapshot.timestamp, float)
