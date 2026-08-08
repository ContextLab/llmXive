"""
Unit tests for the ResourceMonitor class in code/utils.py.
"""
import json
import os
import sys
import time
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import ResourceMonitor, ResourceUsage


class TestResourceMonitor:
    """Tests for the ResourceMonitor class."""

    @pytest.fixture
    def temp_output_dir(self, tmp_path):
        """Create a temporary directory for output files."""
        return tmp_path / "resource_test"

    def test_init_creates_directory(self, temp_output_dir):
        """Test that initialization creates the output directory."""
        monitor = ResourceMonitor(output_dir=temp_output_dir)
        assert temp_output_dir.exists()
        assert monitor.output_dir == temp_output_dir

    def test_start_subject_logs_to_stderr(self, temp_output_dir, capfd):
        """Test that start_subject writes to stderr."""
        monitor = ResourceMonitor(output_dir=temp_output_dir)
        
        with patch('utils.psutil.Process') as mock_process:
            mock_process.return_value.memory_info.return_value.rss = 100 * 1024 * 1024
            monitor.start_subject("sub-001")
        
        captured = capfd.readouterr()
        assert "Started monitoring for subject: sub-001" in captured.err
        assert monitor._current_subject == "sub-001"
        assert monitor._start_time is not None

    def test_record_checkpoint_updates_peak(self, temp_output_dir):
        """Test that record_checkpoint updates peak RAM."""
        monitor = ResourceMonitor(output_dir=temp_output_dir)
        monitor._current_subject = "sub-001"
        monitor._start_time = time.time()
        monitor._peak_ram_mb = 100.0
        
        # Mock higher RAM
        with patch.object(monitor, '_get_current_ram_mb', return_value=150.0):
            monitor.record_checkpoint("test_checkpoint")
        
        assert monitor._peak_ram_mb == 150.0

    def test_finish_subject_creates_record(self, temp_output_dir):
        """Test that finish_subject creates a valid record."""
        monitor = ResourceMonitor(output_dir=temp_output_dir)
        monitor._current_subject = "sub-001"
        monitor._start_time = time.time() - 10  # 10 seconds ago
        monitor._peak_ram_mb = 200.0
        
        with patch.object(monitor, '_get_current_ram_mb', return_value=180.0):
            monitor.finish_subject()
        
        assert len(monitor._measurements) == 1
        record = monitor._measurements[0]
        assert record["subject_id"] == "sub-001"
        assert record["peak_ram_mb"] == 200.0
        assert 9.0 <= record["duration_seconds"] <= 11.0

    def test_save_profile_writes_json(self, temp_output_dir):
        """Test that save_profile writes a valid JSON file."""
        monitor = ResourceMonitor(output_dir=temp_output_dir)
        monitor._current_subject = "sub-001"
        monitor._start_time = time.time() - 5
        monitor._peak_ram_mb = 123.45
        monitor._measurements = [{
            "subject_id": "sub-001",
            "peak_ram_mb": 123.45,
            "start_time": "2024-01-01T00:00:00",
            "end_time": "2024-01-01T00:00:05",
            "duration_seconds": 5.0
        }]
        
        result_path = monitor.save_profile()
        
        assert result_path.exists()
        assert result_path.suffix == ".json"
        
        with open(result_path, 'r') as f:
            data = json.load(f)
        
        assert "generated_at" in data
        assert data["total_subjects"] == 1
        assert len(data["measurements"]) == 1
        assert data["measurements"][0]["subject_id"] == "sub-001"

    def test_get_summary_calculates_correctly(self, temp_output_dir):
        """Test that get_summary calculates correct statistics."""
        monitor = ResourceMonitor(output_dir=temp_output_dir)
        monitor._measurements = [
            {"peak_ram_mb": 100.0, "duration_seconds": 10.0},
            {"peak_ram_mb": 200.0, "duration_seconds": 20.0},
            {"peak_ram_mb": 150.0, "duration_seconds": 15.0}
        ]
        
        summary = monitor.get_summary()
        
        assert summary["avg_peak_ram_mb"] == 150.0
        assert summary["max_peak_ram_mb"] == 200.0
        assert summary["total_duration_seconds"] == 45.0

    def test_get_summary_empty_measurements(self, temp_output_dir):
        """Test that get_summary returns zeros for empty measurements."""
        monitor = ResourceMonitor(output_dir=temp_output_dir)
        
        summary = monitor.get_summary()
        
        assert summary["avg_peak_ram_mb"] == 0.0
        assert summary["max_peak_ram_mb"] == 0.0
        assert summary["total_duration_seconds"] == 0.0

    def test_no_psutil_fallback(self, temp_output_dir):
        """Test fallback behavior when psutil is not available."""
        with patch('utils.PSUTIL_AVAILABLE', False):
            with patch.object(sys, 'platform', 'linux'):
                with patch('builtins.open', mock_open_read_data='VmRSS: 102400 kB\n'):
                    monitor = ResourceMonitor(output_dir=temp_output_dir)
                    ram = monitor._get_current_ram_mb()
                    assert ram == 100.0  # 102400 kB / 1024

    def test_finish_without_start_logs_warning(self, temp_output_dir, capfd):
        """Test that finishing without starting logs a warning."""
        monitor = ResourceMonitor(output_dir=temp_output_dir)
        monitor.finish_subject()
        
        captured = capfd.readouterr()
        assert "No active subject to finish" in captured.err

def mock_open_read_data(data):
    """Helper for mocking file reads."""
    from unittest.mock import mock_open
    m = mock_open(read_data=data)
    return m