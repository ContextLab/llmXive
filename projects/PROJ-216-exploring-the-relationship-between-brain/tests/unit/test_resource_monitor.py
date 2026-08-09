import json
import os
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure the code directory is in the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils import ResourceMonitor, ResourceUsage

class TestResourceMonitor(unittest.TestCase):
    """Unit tests for ResourceMonitor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.monitor = ResourceMonitor()
        self.processed_dir = Path("data/processed")
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        # Clean up any existing profile before test
        profile_path = self.processed_dir / "resource_profile.json"
        if profile_path.exists():
            profile_path.unlink()

    def tearDown(self):
        """Clean up after tests."""
        pass

    def test_start_records_snapshot(self):
        """Test that start() records a snapshot and logs to stderr."""
        with patch.object(self.monitor, '_get_current_ram_gb', return_value=2.5):
            self.monitor.start("sub-001")
            self.assertEqual(len(self.monitor.snapshots), 1)
            self.assertEqual(self.monitor.snapshots[0].subject_id, "sub-001")
            self.assertEqual(self.monitor.snapshots[0].ram_gb, 2.5)

    def test_stop_records_snapshot(self):
        """Test that stop() records a snapshot."""
        with patch.object(self.monitor, '_get_current_ram_gb', return_value=3.0):
            self.monitor.start("sub-002")
            self.monitor.stop("sub-002")
            # Should have 2 snapshots (start and stop)
            self.assertEqual(len(self.monitor.snapshots), 2)

    @patch('builtins.print')
    def test_error_logging(self, mock_print):
        """Test that stop() with error logs to stderr."""
        self.monitor.stop("sub-003", error="Test error")
        mock_print.assert_called_with(
            "[ResourceMonitor] Error for sub-003: Test error",
            file=sys.stderr
        )

    def test_finalize_writes_json_with_correct_schema(self):
        """
        Test that finalize() writes resource_profile.json with the correct schema.
        This test simulates a mock process by mocking RAM readings and timing.
        """
        # Mock RAM readings
        ram_values = [1.5, 2.0, 2.5, 2.0]
        ram_iter = iter(ram_values)
        
        def mock_ram():
            try:
                return next(ram_iter)
            except StopIteration:
                return 0.0

        with patch.object(self.monitor, '_get_current_ram_gb', side_effect=mock_ram):
            # Simulate monitoring a mock process with multiple subjects
            self.monitor.start("sub-001")
            time.sleep(0.01) # Tiny delay to ensure time difference
            self.monitor.stop("sub-001")
            
            self.monitor.start("sub-002")
            time.sleep(0.01)
            self.monitor.stop("sub-002")
            
            # Finalize should write the file
            self.monitor.finalize()

        # Verify file exists
        profile_path = self.processed_dir / "resource_profile.json"
        self.assertTrue(profile_path.exists(), "resource_profile.json was not created")

        # Load and verify schema
        with open(profile_path, 'r') as f:
            data = json.load(f)

        # Check required top-level keys
        self.assertIn("peak_ram_gb", data)
        self.assertIn("total_runtime_hours", data)
        self.assertIn("subject_count", data)
        
        # Verify types
        self.assertIsInstance(data["peak_ram_gb"], float)
        self.assertIsInstance(data["total_runtime_hours"], float)
        self.assertIsInstance(data["subject_count"], int)

        # Verify values based on our mock data
        # Peak should be 2.5 (from our mock list)
        self.assertEqual(data["peak_ram_gb"], 2.5)
        
        # Subject count should be 2
        self.assertEqual(data["subject_count"], 2)

        # Verify runtime is non-negative
        self.assertGreaterEqual(data["total_runtime_hours"], 0.0)

        # Verify snapshots list exists and has correct structure
        self.assertIn("snapshots", data)
        self.assertIsInstance(data["snapshots"], list)
        self.assertGreater(len(data["snapshots"]), 0)

        for snapshot in data["snapshots"]:
            self.assertIn("subject_id", snapshot)
            self.assertIn("ram_gb", snapshot)
            self.assertIn("timestamp", snapshot)
            self.assertIsInstance(snapshot["subject_id"], str)
            self.assertIsInstance(snapshot["ram_gb"], float)
            self.assertIsInstance(snapshot["timestamp"], float)

        # Verify subject_peak_ram_gb exists
        self.assertIn("subject_peak_ram_gb", data)
        self.assertIsInstance(data["subject_peak_ram_gb"], dict)
        self.assertEqual(len(data["subject_peak_ram_gb"]), 2)
        self.assertEqual(data["subject_peak_ram_gb"]["sub-001"], 2.0) # max of 1.5, 2.0
        self.assertEqual(data["subject_peak_ram_gb"]["sub-002"], 2.5) # max of 2.5, 2.0

    def test_finalize_empty_snapshots(self):
        """Test finalize behavior when no snapshots were recorded."""
        # Ensure no snapshots
        self.monitor.snapshots = []
        self.monitor.start_time = None
        
        self.monitor.finalize()
        
        profile_path = self.processed_dir / "resource_profile.json"
        with open(profile_path, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(data["peak_ram_gb"], 0.0)
        self.assertEqual(data["total_runtime_hours"], 0.0)
        self.assertEqual(data["subject_count"], 0)
        self.assertEqual(data["snapshots"], [])

if __name__ == '__main__':
    unittest.main()