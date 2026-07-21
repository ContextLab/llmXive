"""
Unit tests for the trajectory schema and writer.
"""

import unittest
import json
import os
import tempfile
import shutil
from datetime import datetime

# Add project root to path if running standalone
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from results.trajectory_schema import TrajectoryEntry, write_trajectory, read_trajectory
from config import PathConfig


class TestTrajectoryEntry(unittest.TestCase):
    """Tests for the TrajectoryEntry Pydantic model."""

    def test_valid_entry_creation(self):
        """Test creating a valid trajectory entry."""
        entry = TrajectoryEntry(
            cycle_number=1,
            timestamp=datetime.now().isoformat(),
            param_count=124000000,
            gsm8k_accuracy=0.45,
            arc_accuracy=0.52,
            wikitext2_ece=0.12,
            flops=1500000000000,
            training_time_seconds=3600.5,
            modification_type="layer_addition",
            modification_magnitude=1.0,
            status="completed"
        )
        self.assertEqual(entry.cycle_number, 1)
        self.assertEqual(entry.param_count, 124000000)
        self.assertEqual(entry.status, "completed")

    def test_invalid_metric_range(self):
        """Test that metrics outside 0-1 range raise error."""
        with self.assertRaises(ValueError):
            TrajectoryEntry(
                cycle_number=1,
                timestamp=datetime.now().isoformat(),
                param_count=124000000,
                gsm8k_accuracy=1.5,  # Invalid
                arc_accuracy=0.52,
                wikitext2_ece=0.12,
                flops=1500000000000,
                training_time_seconds=3600.5
            )

    def test_negative_flops(self):
        """Test that negative FLOPs raise error."""
        with self.assertRaises(ValueError):
            TrajectoryEntry(
                cycle_number=1,
                timestamp=datetime.now().isoformat(),
                param_count=124000000,
                gsm8k_accuracy=0.45,
                arc_accuracy=0.52,
                wikitext2_ece=0.12,
                flops=-100,  # Invalid
                training_time_seconds=3600.5
            )

    def test_invalid_timestamp(self):
        """Test that invalid timestamp raises error."""
        with self.assertRaises(ValueError):
            TrajectoryEntry(
                cycle_number=1,
                timestamp="not-a-date",
                param_count=124000000,
                gsm8k_accuracy=0.45,
                arc_accuracy=0.52,
                wikitext2_ece=0.12,
                flops=1500000000000,
                training_time_seconds=3600.5
            )

    def test_model_dump(self):
        """Test that model_dump produces correct dictionary."""
        entry = TrajectoryEntry(
            cycle_number=1,
            timestamp="2024-01-01T00:00:00",
            param_count=124000000,
            gsm8k_accuracy=0.45,
            arc_accuracy=0.52,
            wikitext2_ece=0.12,
            flops=1500000000000,
            training_time_seconds=3600.5
        )
        data = entry.model_dump()
        self.assertIsInstance(data, dict)
        self.assertEqual(data['cycle_number'], 1)
        self.assertIn('timestamp', data)


class TestWriteReadTrajectory(unittest.TestCase):
    """Tests for trajectory file I/O."""

    def setUp(self):
        """Create a temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
        # Mock the PathConfig to use temp dir
        self.original_results_dir = PathConfig.results_dir
        PathConfig.results_dir = self.temp_dir

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)
        # Restore original PathConfig
        PathConfig.results_dir = self.original_results_dir

    def test_write_new_trajectory(self):
        """Test writing a new trajectory file."""
        entry = TrajectoryEntry(
            cycle_number=1,
            timestamp="2024-01-01T00:00:00",
            param_count=124000000,
            gsm8k_accuracy=0.45,
            arc_accuracy=0.52,
            wikitext2_ece=0.12,
            flops=1500000000000,
            training_time_seconds=3600.5
        )
        
        path = write_trajectory([entry])
        
        self.assertTrue(os.path.exists(path))
        with open(path, 'r') as f:
            data = json.load(f)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['cycle_number'], 1)

    def test_append_to_existing_trajectory(self):
        """Test appending entries to an existing trajectory file."""
        entry1 = TrajectoryEntry(
            cycle_number=1,
            timestamp="2024-01-01T00:00:00",
            param_count=124000000,
            gsm8k_accuracy=0.45,
            arc_accuracy=0.52,
            wikitext2_ece=0.12,
            flops=1500000000000,
            training_time_seconds=3600.5
        )
        
        # Write first entry
        write_trajectory([entry1])
        
        # Append second entry
        entry2 = TrajectoryEntry(
            cycle_number=2,
            timestamp="2024-01-02T00:00:00",
            param_count=130000000,
            gsm8k_accuracy=0.47,
            arc_accuracy=0.54,
            wikitext2_ece=0.10,
            flops=1600000000000,
            training_time_seconds=3700.5
        )
        
        write_trajectory([entry2])
        
        # Read back and verify
        entries = read_trajectory()
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].cycle_number, 1)
        self.assertEqual(entries[1].cycle_number, 2)

    def test_read_empty_trajectory(self):
        """Test reading when file doesn't exist."""
        entries = read_trajectory()
        self.assertEqual(entries, [])

    def test_read_trajectory_with_invalid_json(self):
        """Test reading a corrupted file."""
        # Create a file with invalid JSON
        traj_path = os.path.join(self.temp_dir, "trajectory.json")
        with open(traj_path, 'w') as f:
            f.write("{ invalid json }")
        
        with self.assertRaises(RuntimeError):
            read_trajectory()


if __name__ == '__main__':
    unittest.main()