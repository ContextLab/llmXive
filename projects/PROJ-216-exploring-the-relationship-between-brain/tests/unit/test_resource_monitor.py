import json
import os
import sys
import time
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the class under test
from code.utils import ResourceMonitor, ResourceUsage


class TestResourceMonitor(unittest.TestCase):
    """Unit tests for the ResourceMonitor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.monitor = ResourceMonitor()
        # Ensure the output directory exists for tests
        self.processed_dir = Path("data/processed")
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up after tests."""
        # Clean up generated files if any
        profile_path = self.processed_dir / "resource_profile.json"
        if profile_path.exists():
            profile_path.unlink()

    def test_init(self):
        """Test initialization of ResourceMonitor."""
        self.assertEqual(self.monitor.snapshots, [])
        self.assertIsNone(self.monitor.start_time)
        self.assertEqual(self.monitor.subject_start_times, {})

    @patch('code.utils.ResourceMonitor._get_current_ram_gb')
    def test_start_logs_snapshot(self, mock_get_ram):
        """Test that start() logs a snapshot and sets start time."""
        mock_get_ram.return_value = 2.5
        subject_id = "sub-001"
        
        self.monitor.start(subject_id)
        
        self.assertIn(subject_id, self.monitor.subject_start_times)
        self.assertIsNotNone(self.monitor.start_time)
        self.assertEqual(len(self.monitor.snapshots), 1)
        self.assertEqual(self.monitor.snapshots[0].subject_id, subject_id)
        self.assertEqual(self.monitor.snapshots[0].ram_gb, 2.5)

    @patch('code.utils.ResourceMonitor._get_current_ram_gb')
    def test_stop_logs_snapshot(self, mock_get_ram):
        """Test that stop() logs a snapshot and removes start time."""
        mock_get_ram.return_value = 3.0
        subject_id = "sub-002"
        
        # First start to register the subject
        self.monitor.start(subject_id)
        initial_count = len(self.monitor.snapshots)
        
        # Now stop
        self.monitor.stop(subject_id)
        
        self.assertNotIn(subject_id, self.monitor.subject_start_times)
        self.assertEqual(len(self.monitor.snapshots), initial_count + 1)
        self.assertEqual(self.monitor.snapshots[-1].subject_id, subject_id)

    @patch('code.utils.ResourceMonitor._get_current_ram_gb')
    def test_stop_with_error_prints_to_stderr(self, mock_get_ram):
        """Test that stop() prints error to stderr if provided."""
        mock_get_ram.return_value = 1.0
        subject_id = "sub-003"
        error_msg = "Simulated failure"
        
        # Capture stderr
        from io import StringIO
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            self.monitor.start(subject_id)
            self.monitor.stop(subject_id, error=error_msg)
            
            stderr_output = sys.stderr.getvalue()
            self.assertIn(f"[ResourceMonitor] Error for {subject_id}: {error_msg}", stderr_output)
        finally:
            sys.stderr = old_stderr

    @patch('code.utils.ResourceMonitor._get_current_ram_gb')
    def test_finalize_writes_json(self, mock_get_ram):
        """Test that finalize() writes the resource profile to JSON."""
        # Simulate multiple snapshots
        mock_get_ram.side_effect = [1.0, 2.0, 1.5, 3.0]
        
        self.monitor.start("sub-001")
        time.sleep(0.01) # Ensure timestamp difference
        self.monitor.stop("sub-001")
        
        self.monitor.start("sub-002")
        time.sleep(0.01)
        self.monitor.stop("sub-002")
        
        # Finalize
        self.monitor.finalize()
        
        profile_path = self.processed_dir / "resource_profile.json"
        self.assertTrue(profile_path.exists())
        
        with open(profile_path, 'r') as f:
            profile = json.load(f)
        
        self.assertIn("peak_ram_gb", profile)
        self.assertIn("total_runtime_hours", profile)
        self.assertIn("subject_count", profile)
        self.assertIn("snapshots", profile)
        
        # Verify peak RAM is the max of the simulated values
        self.assertEqual(profile["peak_ram_gb"], 3.0)
        self.assertEqual(profile["subject_count"], 2)

    def test_finalize_empty(self):
        """Test finalize() when no snapshots were collected."""
        self.monitor.finalize()
        
        profile_path = self.processed_dir / "resource_profile.json"
        self.assertTrue(profile_path.exists())
        
        with open(profile_path, 'r') as f:
            profile = json.load(f)
        
        self.assertEqual(profile["peak_ram_gb"], 0.0)
        self.assertEqual(profile["total_runtime_hours"], 0.0)
        self.assertEqual(profile["subject_count"], 0)
        self.assertEqual(profile["snapshots"], [])

    @patch('code.utils.ResourceMonitor._get_current_ram_gb')
    def test_log_snapshot_format(self, mock_get_ram):
        """Test that log_snapshot prints the correct format to stderr."""
        mock_get_ram.return_value = 4.567
        subject_id = "sub-004"
        
        # Capture stderr
        from io import StringIO
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            self.monitor.log_snapshot(subject_id)
            stderr_output = sys.stderr.getvalue()
            
            # Check format: [ResourceMonitor] sub-004: RAM usage = 4.57 GB
            self.assertIn(f"[ResourceMonitor] {subject_id}: RAM usage =", stderr_output)
            self.assertIn("GB", stderr_output)
            # Check rounding to 2 decimal places
            self.assertIn("4.57", stderr_output)
        finally:
            sys.stderr = old_stderr

    def test_subject_peak_aggregation(self):
        """Test that finalize correctly aggregates peak RAM per subject."""
        # Mock RAM values: sub-001 goes 1.0 -> 5.0, sub-002 goes 2.0 -> 3.0
        # Expected peak: 5.0 (from sub-001)
        
        with patch.object(self.monitor, '_get_current_ram_gb', side_effect=[1.0, 5.0, 2.0, 3.0]):
            self.monitor.start("sub-001")
            self.monitor.stop("sub-001")
            self.monitor.start("sub-002")
            self.monitor.stop("sub-002")
            
            self.monitor.finalize()
            
            profile_path = self.processed_dir / "resource_profile.json"
            with open(profile_path, 'r') as f:
                profile = json.load(f)
            
            self.assertEqual(profile["peak_ram_gb"], 5.0)
            self.assertEqual(profile["subject_peak_ram_gb"]["sub-001"], 5.0)
            self.assertEqual(profile["subject_peak_ram_gb"]["sub-002"], 3.0)

    def test_runtime_calculation(self):
        """Test that total_runtime_hours is calculated correctly."""
        start_time = time.time()
        self.monitor.start_time = start_time
        
        # Simulate a short duration
        time.sleep(0.1)
        
        self.monitor.finalize()
        
        profile_path = self.processed_dir / "resource_profile.json"
        with open(profile_path, 'r') as f:
            profile = json.load(f)
        
        # Runtime should be at least 0.1 seconds (0.1/3600 hours)
        expected_min_hours = 0.1 / 3600.0
        self.assertGreaterEqual(profile["total_runtime_hours"], expected_min_hours)

if __name__ == '__main__':
    unittest.main()