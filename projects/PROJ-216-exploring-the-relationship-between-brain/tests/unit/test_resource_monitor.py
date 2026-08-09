import json
import os
import sys
import time
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Ensure we import from the project code directory
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from utils import ResourceMonitor, ResourceUsage

class TestResourceMonitor:
    """Unit tests for ResourceMonitor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.processed_dir = Path(self.test_dir) / "data" / "processed"
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch('utils.ResourceMonitor._get_current_ram_gb')
    def test_log_snapshot_creates_entry(self, mock_ram):
        """Test that log_snapshot creates a ResourceUsage entry and logs to stderr."""
        mock_ram.return_value = 2.5
        
        monitor = ResourceMonitor()
        # Override processed_dir for test
        monitor.processed_dir = self.processed_dir
        
        with patch('builtins.print') as mock_print:
            monitor.log_snapshot("sub-001")
        
        assert len(monitor.snapshots) == 1
        assert monitor.snapshots[0].subject_id == "sub-001"
        assert monitor.snapshots[0].ram_gb == 2.5
        mock_print.assert_called_once()
        assert "sub-001" in str(mock_print.call_args)

    @patch('utils.ResourceMonitor._get_current_ram_gb')
    def test_start_and_stop(self, mock_ram):
        """Test start and stop methods."""
        mock_ram.return_value = 3.0
        
        monitor = ResourceMonitor()
        monitor.processed_dir = self.processed_dir
        
        with patch('builtins.print'):
            monitor.start("sub-002")
            assert "sub-002" in monitor.subject_start_times
            assert len(monitor.snapshots) == 1
            
            monitor.stop("sub-002")
            assert "sub-002" not in monitor.subject_start_times
            assert len(monitor.snapshots) == 2  # One at start, one at stop

    @patch('utils.ResourceMonitor._get_current_ram_gb')
    def test_finalize_writes_json(self, mock_ram):
        """Test that finalize writes resource_profile.json with correct schema."""
        mock_ram.return_value = 4.0
        
        monitor = ResourceMonitor()
        monitor.processed_dir = self.processed_dir
        
        with patch('builtins.print'):
            monitor.start("sub-003")
            time.sleep(0.01)
            mock_ram.return_value = 4.5
            monitor.log_snapshot("sub-003")
            monitor.stop("sub-003")
            monitor.finalize()
        
        output_path = monitor.processed_dir / "resource_profile.json"
        assert output_path.exists(), "resource_profile.json was not created"
        
        with open(output_path, 'r') as f:
            profile = json.load(f)
        
        # Verify schema
        assert "peak_ram_gb" in profile
        assert "total_runtime_hours" in profile
        assert "subject_count" in profile
        assert "subject_peak_ram_gb" in profile
        assert "snapshots" in profile
        
        # Verify values
        assert profile["peak_ram_gb"] >= 4.0
        assert profile["subject_count"] == 1
        assert len(profile["snapshots"]) == 2
        assert "sub-003" in profile["subject_peak_ram_gb"]

    @patch('utils.ResourceMonitor._get_current_ram_gb')
    def test_finalize_empty_snapshots(self, mock_ram):
        """Test finalize behavior when no snapshots were recorded."""
        monitor = ResourceMonitor()
        monitor.processed_dir = self.processed_dir
        
        monitor.finalize()
        
        output_path = monitor.processed_dir / "resource_profile.json"
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            profile = json.load(f)
        
        assert profile["peak_ram_gb"] == 0.0
        assert profile["total_runtime_hours"] == 0.0
        assert profile["subject_count"] == 0
        assert profile["snapshots"] == []

    @patch('utils.ResourceMonitor._get_current_ram_gb')
    def test_multiple_subjects_aggregation(self, mock_ram):
        """Test aggregation of multiple subjects."""
        mock_ram.return_value = 2.0
        
        monitor = ResourceMonitor()
        monitor.processed_dir = self.processed_dir
        
        with patch('builtins.print'):
            monitor.start("sub-A")
            monitor.log_snapshot("sub-A")
            monitor.stop("sub-A")
            
            mock_ram.return_value = 5.0
            monitor.start("sub-B")
            monitor.log_snapshot("sub-B")
            monitor.stop("sub-B")
            
            monitor.finalize()
        
        output_path = monitor.processed_dir / "resource_profile.json"
        with open(output_path, 'r') as f:
            profile = json.load(f)
        
        assert profile["subject_count"] == 2
        assert profile["peak_ram_gb"] == 5.0
        assert "sub-A" in profile["subject_peak_ram_gb"]
        assert "sub-B" in profile["subject_peak_ram_gb"]

    def test_error_logging_on_stop(self):
        """Test that errors are logged to stderr on stop."""
        monitor = ResourceMonitor()
        
        with patch('builtins.print') as mock_print:
            monitor.stop("sub-004", error="Simulated failure")
        
        mock_print.assert_called_once()
        call_args = str(mock_print.call_args)
        assert "sub-004" in call_args
        assert "Simulated failure" in call_args
        assert "[ResourceMonitor]" in call_args
