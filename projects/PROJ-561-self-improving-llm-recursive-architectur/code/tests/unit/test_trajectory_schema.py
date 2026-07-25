"""
Unit tests for the trajectory schema and writer (T029).
"""
import unittest
import os
import json
import tempfile
from datetime import datetime

from results.trajectory_schema import (
    TrajectoryEntry,
    write_trajectory,
    read_trajectory,
    get_latest_entry
)


class TestTrajectorySchema(unittest.TestCase):
    """Tests for TrajectoryEntry model and I/O functions."""

    def setUp(self):
        """Create a temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test_trajectory.json")

    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        os.rmdir(self.temp_dir)

    def test_trajectory_entry_creation(self):
        """Test creating a valid TrajectoryEntry."""
        entry = TrajectoryEntry(
            cycle_number=1,
            timestamp=datetime.now().isoformat(),
            param_count=124000000,
            gsm8k_accuracy=0.15,
            arc_accuracy=0.45,
            wikitext2_ece=0.12,
            flops_total=1e12,
            training_time_seconds=3600.5,
            modification_type="layer_add",
            modification_magnitude=1,
            distinctness_valid=True
        )
        self.assertEqual(entry.cycle_number, 1)
        self.assertEqual(entry.modification_type, "layer_add")
        self.assertTrue(entry.distinctness_valid)

    def test_trajectory_entry_validation_negative_cycle(self):
        """Test that negative cycle numbers are rejected."""
        with self.assertRaises(ValueError):
            TrajectoryEntry(
                cycle_number=0,
                timestamp=datetime.now().isoformat(),
                param_count=100,
                gsm8k_accuracy=0.1,
                arc_accuracy=0.1,
                wikitext2_ece=0.1,
                flops_total=1.0,
                training_time_seconds=1.0,
                modification_type="test",
                modification_magnitude=1,
                distinctness_valid=True
            )

    def test_write_and_read_trajectory(self):
        """Test writing entries to file and reading them back."""
        entries = [
            TrajectoryEntry(
                cycle_number=1,
                timestamp=datetime.now().isoformat(),
                param_count=124000000,
                gsm8k_accuracy=0.15,
                arc_accuracy=0.45,
                wikitext2_ece=0.12,
                flops_total=1e12,
                training_time_seconds=3600.0,
                modification_type="layer_add",
                modification_magnitude=1,
                distinctness_valid=True
            ),
            TrajectoryEntry(
                cycle_number=2,
                timestamp=datetime.now().isoformat(),
                param_count=130000000,
                gsm8k_accuracy=0.18,
                arc_accuracy=0.48,
                wikitext2_ece=0.10,
                flops_total=1.1e12,
                training_time_seconds=3700.0,
                modification_type="head_count_change",
                modification_magnitude=2,
                distinctness_valid=True
            )
        ]

        # Write
        written_path = write_trajectory(entries, self.test_file)
        self.assertTrue(os.path.exists(written_path))

        # Read back
        read_entries = read_trajectory(self.test_file)
        self.assertEqual(len(read_entries), 2)
        self.assertEqual(read_entries[0].cycle_number, 1)
        self.assertEqual(read_entries[1].modification_type, "head_count_change")

    def test_read_nonexistent_file(self):
        """Test reading from a file that doesn't exist returns empty list."""
        entries = read_trajectory("/tmp/does_not_exist_trajectory.json")
        self.assertEqual(entries, [])

    def test_get_latest_entry(self):
        """Test retrieving the latest entry."""
        entries = [
            TrajectoryEntry(
                cycle_number=1,
                timestamp=datetime.now().isoformat(),
                param_count=100,
                gsm8k_accuracy=0.1,
                arc_accuracy=0.1,
                wikitext2_ece=0.1,
                flops_total=1.0,
                training_time_seconds=1.0,
                modification_type="test",
                modification_magnitude=1,
                distinctness_valid=True
            ),
            TrajectoryEntry(
                cycle_number=2,
                timestamp=datetime.now().isoformat(),
                param_count=100,
                gsm8k_accuracy=0.2,
                arc_accuracy=0.2,
                wikitext2_ece=0.2,
                flops_total=2.0,
                training_time_seconds=2.0,
                modification_type="test",
                modification_magnitude=1,
                distinctness_valid=True
            )
        ]
        write_trajectory(entries, self.test_file)
        latest = get_latest_entry(self.test_file)
        self.assertIsNotNone(latest)
        self.assertEqual(latest.cycle_number, 2)

    def test_get_latest_entry_empty_file(self):
        """Test get_latest_entry on empty file."""
        # Create empty file
        with open(self.test_file, 'w') as f:
            json.dump([], f)
        
        latest = get_latest_entry(self.test_file)
        self.assertIsNone(latest)

    def test_json_structure(self):
        """Verify the JSON structure matches expected keys."""
        entry = TrajectoryEntry(
            cycle_number=1,
            timestamp=datetime.now().isoformat(),
            param_count=124000000,
            gsm8k_accuracy=0.15,
            arc_accuracy=0.45,
            wikitext2_ece=0.12,
            flops_total=1e12,
            training_time_seconds=3600.0,
            modification_type="layer_add",
            modification_magnitude=1,
            distinctness_valid=True
        )
        write_trajectory([entry], self.test_file)
        
        with open(self.test_file, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(len(data), 1)
        required_keys = [
            "cycle_number", "timestamp", "param_count", "gsm8k_accuracy",
            "arc_accuracy", "wikitext2_ece", "flops_total", "training_time_seconds",
            "modification_type", "modification_magnitude", "distinctness_valid"
        ]
        for key in required_keys:
            self.assertIn(key, data[0])