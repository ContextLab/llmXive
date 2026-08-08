"""
Unit tests for the ResourceMonitor class in code/utils.py.
"""
import json
import os
import sys
import time
import pytest
import tempfile
import shutil

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils import ResourceMonitor


class TestResourceMonitor:
    """Tests for ResourceMonitor functionality."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for output files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_init_creates_directory(self, temp_output_dir):
        """Test that __init__ creates the output directory if it doesn't exist."""
        monitor = ResourceMonitor(output_dir=temp_output_dir)
        assert monitor.output_dir.exists()
        assert monitor.output_dir == temp_output_dir

    def test_start_subject_logs_to_stderr(self, capfd, temp_output_dir):
        """Test that start_subject writes to stderr."""
        monitor = ResourceMonitor(output_dir=temp_output_dir)
        monitor.start_subject("sub-001")
        
        captured = capfd.readouterr()
        assert "sub-001" in captured.err
        assert "Started monitoring" in captured.err
        assert monitor._current_subject == "sub-001"
        assert monitor._start_time is not None

    def test_record_checkpoint_updates_peak(self, temp_output_dir):
        """Test that record_checkpoint updates peak RAM if current is higher."""
        # Note: We can't easily simulate higher RAM, but we can test the logic
        # by checking that the method doesn't crash and logs if label is provided
        monitor = ResourceMonitor(output_dir=temp_output_dir)
        monitor.start_subject("sub-001")
        
        # Record a checkpoint without label (should not log)
        monitor.record_checkpoint()
        
        # Record a checkpoint with label (should log)
        monitor.record_checkpoint("test_checkpoint")
        
        captured = capfd.readouterr()
        assert "test_checkpoint" in captured.err
        
        monitor.finish_subject()

    def test_finish_subject_creates_record(self, temp_output_dir):
        """Test that finish_subject creates a valid record."""
        monitor = ResourceMonitor(output_dir=temp_output_dir)
        monitor.start_subject("sub-001")
        time.sleep(0.1)  # Ensure some duration
        monitor.finish_subject()
        
        assert len(monitor._measurements) == 1
        record = monitor._measurements[0]
        
        assert record["subject_id"] == "sub-001"
        assert "peak_ram_mb" in record
        assert "start_time" in record
        assert "end_time" in record
        assert "duration_seconds" in record
        assert record["duration_seconds"] >= 0.1

    def test_finish_subject_without_start(self, capfd, temp_output_dir):
        """Test that finish_subject handles the case where no subject was started."""
        monitor = ResourceMonitor(output_dir=temp_output_dir)
        monitor.finish_subject()
        
        captured = capfd.readouterr()
        assert "No active subject to finish" in captured.err
        assert len(monitor._measurements) == 0

    def test_save_profile_creates_json(self, temp_output_dir):
        """Test that save_profile writes a valid JSON file."""
        monitor = ResourceMonitor(output_dir=temp_output_dir)
        monitor.start_subject("sub-001")
        time.sleep(0.1)
        monitor.finish_subject()
        
        path = monitor.save_profile()
        
        assert path.exists()
        assert path.suffix == ".json"
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        assert "generated_at" in data
        assert "total_subjects" in data
        assert "measurements" in data
        assert data["total_subjects"] == 1
        assert len(data["measurements"]) == 1

    def test_get_summary_empty(self, temp_output_dir):
        """Test get_summary returns zeros when no measurements."""
        monitor = ResourceMonitor(output_dir=temp_output_dir)
        summary = monitor.get_summary()
        
        assert summary["avg_peak_ram_mb"] == 0.0
        assert summary["max_peak_ram_mb"] == 0.0
        assert summary["total_duration_seconds"] == 0.0

    def test_get_summary_with_data(self, temp_output_dir):
        """Test get_summary calculates correct statistics."""
        monitor = ResourceMonitor(output_dir=temp_output_dir)
        
        # Add two mock measurements
        monitor._measurements = [
            {"peak_ram_mb": 100.0, "duration_seconds": 10.0},
            {"peak_ram_mb": 200.0, "duration_seconds": 20.0}
        ]
        
        summary = monitor.get_summary()
        
        assert summary["avg_peak_ram_mb"] == 150.0
        assert summary["max_peak_ram_mb"] == 200.0
        assert summary["total_duration_seconds"] == 30.0

    def test_integration_full_flow(self, capfd, temp_output_dir):
        """Test the complete flow of monitoring a subject."""
        monitor = ResourceMonitor(output_dir=temp_output_dir)
        
        # Start subject
        monitor.start_subject("sub-test-123")
        initial_err = capfd.readouterr().err
        assert "sub-test-123" in initial_err
        
        # Record checkpoint
        monitor.record_checkpoint("mid_process")
        checkpoint_err = capfd.readouterr().err
        assert "mid_process" in checkpoint_err
        
        # Finish subject
        time.sleep(0.1)
        monitor.finish_subject()
        finish_err = capfd.readouterr().err
        assert "Finished sub-test-123" in finish_err
        
        # Save profile
        profile_path = monitor.save_profile()
        save_err = capfd.readouterr().err
        assert "Profile saved" in save_err
        
        # Verify file content
        with open(profile_path, 'r') as f:
            data = json.load(f)
        
        assert data["total_subjects"] == 1
        assert data["measurements"][0]["subject_id"] == "sub-test-123"
        assert data["measurements"][0]["duration_seconds"] >= 0.1