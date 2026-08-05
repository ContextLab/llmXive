"""
Unit tests for the ResourceMonitor class in code/utils.py.
"""
import json
import os
import sys
import tempfile
import time
from pathlib import Path
import pytest

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import ResourceMonitor


class TestResourceMonitor:
    def test_initialization_creates_dir(self):
        """Test that __init__ creates the output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "new_dir"
            monitor = ResourceMonitor(output_dir=output_dir)
            
            assert output_dir.exists()
            assert monitor.output_file == output_dir / "resource_profile.json"

    def test_start_subject_logs_to_stderr(self, capsys):
        """Test that start_subject writes to stderr."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor = ResourceMonitor(output_dir=Path(tmpdir))
            monitor.start_subject("sub-001")
            
            captured = capsys.readouterr()
            assert "Started monitoring for subject: sub-001" in captured.err
            assert monitor._current_subject == "sub-001"
            assert monitor._start_time is not None

    def test_finish_subject_creates_record(self):
        """Test that finish_subject creates a valid record in memory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor = ResourceMonitor(output_dir=Path(tmpdir))
            monitor.start_subject("sub-002")
            time.sleep(0.1)  # Ensure duration > 0
            monitor.finish_subject()
            
            assert len(monitor._measurements) == 1
            record = monitor._measurements[0]
            assert record["subject_id"] == "sub-002"
            assert "peak_ram_mb" in record
            assert record["duration_seconds"] > 0
            assert record["start_time"] is not None
            assert record["end_time"] is not None

    def test_save_profile_writes_json(self):
        """Test that save_profile writes a valid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "resource_profile.json"
            monitor = ResourceMonitor(output_dir=Path(tmpdir))
            
            monitor.start_subject("sub-003")
            monitor.finish_subject()
            monitor.save_profile()
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert "generated_at" in data
            assert "total_subjects" in data
            assert data["total_subjects"] == 1
            assert "measurements" in data
            assert len(data["measurements"]) == 1

    def test_get_summary_calculates_stats(self):
        """Test that get_summary returns correct aggregated stats."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor = ResourceMonitor(output_dir=Path(tmpdir))
            
            # Mock measurements directly to ensure specific values for testing
            monitor._measurements = [
                {"subject_id": "s1", "peak_ram_mb": 100.0, "duration_seconds": 10.0},
                {"subject_id": "s2", "peak_ram_mb": 200.0, "duration_seconds": 20.0}
            ]
            
            summary = monitor.get_summary()
            
            assert summary["avg_peak_ram_mb"] == 150.0
            assert summary["max_peak_ram_mb"] == 200.0
            assert summary["total_duration_seconds"] == 30.0

    def test_no_subject_to_finish(self, capsys):
        """Test behavior when finish_subject is called without start_subject."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor = ResourceMonitor(output_dir=Path(tmpdir))
            monitor.finish_subject()
            
            captured = capsys.readouterr()
            assert "No active subject to finish" in captured.err