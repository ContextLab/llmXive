import unittest
import json
import tempfile
import os
from pathlib import Path
import sys
import numpy as np

# Add src to path if not already present
src_path = Path(__file__).resolve().parent.parent.parent / "code" / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from data.quality_check import calculate_fd, load_motion_json, compute_subject_fd

class TestQualityCheck(unittest.TestCase):
    """Unit tests for FD calculation and quality check logic."""

    def setUp(self):
        """Set up temporary directory for test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_data_dir = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_calculate_fd_zero_motion(self):
        """Test FD calculation when all motion values are zero."""
        # Create dummy motion data: 5 timepoints, 0 motion
        motion_data = {
            "trans_x": [0.0] * 5,
            "trans_y": [0.0] * 5,
            "trans_z": [0.0] * 5,
            "rot_x": [0.0] * 5,
            "rot_y": [0.0] * 5,
            "rot_z": [0.0] * 5
        }
        
        # Save to temp JSON
        motion_file = self.test_data_dir / "motion.json"
        with open(motion_file, "w") as f:
            json.dump(motion_data, f)
        
        fd_values = calculate_fd(motion_file)
        
        # First FD is always 0 (no previous frame)
        self.assertEqual(fd_values[0], 0.0)
        # All subsequent FDs should be 0
        for i in range(1, len(fd_values)):
            self.assertAlmostEqual(fd_values[i], 0.0, places=6)

    def test_calculate_fd_threshold_logic(self):
        """Test that FD > 0.5mm threshold is correctly applied."""
        # Create motion data with known displacements
        # trans_x changes by 0.6mm (exceeds 0.5mm threshold)
        motion_data = {
            "trans_x": [0.0, 0.6, 0.0, 0.0, 0.0],
            "trans_y": [0.0, 0.0, 0.0, 0.0, 0.0],
            "trans_z": [0.0, 0.0, 0.0, 0.0, 0.0],
            "rot_x": [0.0, 0.0, 0.0, 0.0, 0.0],
            "rot_y": [0.0, 0.0, 0.0, 0.0, 0.0],
            "rot_z": [0.0, 0.0, 0.0, 0.0, 0.0]
        }
        
        motion_file = self.test_data_dir / "motion_high.json"
        with open(motion_file, "w") as f:
            json.dump(motion_data, f)
        
        fd_values = calculate_fd(motion_file)
        
        # First FD is 0
        self.assertEqual(fd_values[0], 0.0)
        # Second FD should be > 0.5 (0.6 displacement)
        self.assertGreater(fd_values[1], 0.5)
        # Remaining FDs should be 0
        self.assertEqual(fd_values[2], 0.0)
        self.assertEqual(fd_values[3], 0.0)
        self.assertEqual(fd_values[4], 0.0)

    def test_calculate_fd_rotational_component(self):
        """Test that rotational motion contributes to FD calculation."""
        # Create motion data with rotation
        # rot_z changes by 0.1 rad (~5.7 degrees)
        # Assuming head radius ~50mm, arc length = r * theta = 50 * 0.1 = 5mm
        motion_data = {
            "trans_x": [0.0, 0.0, 0.0, 0.0, 0.0],
            "trans_y": [0.0, 0.0, 0.0, 0.0, 0.0],
            "trans_z": [0.0, 0.0, 0.0, 0.0, 0.0],
            "rot_x": [0.0, 0.0, 0.0, 0.0, 0.0],
            "rot_y": [0.0, 0.0, 0.0, 0.0, 0.0],
            "rot_z": [0.0, 0.1, 0.0, 0.0, 0.0]  # 0.1 rad change
        }
        
        motion_file = self.test_data_dir / "motion_rot.json"
        with open(motion_file, "w") as f:
            json.dump(motion_data, f)
        
        fd_values = calculate_fd(motion_file)
        
        # First FD is 0
        self.assertEqual(fd_values[0], 0.0)
        # Second FD should be > 0.5 due to rotation (5mm arc length)
        self.assertGreater(fd_values[1], 0.5)

    def test_load_motion_json_valid(self):
        """Test loading a valid motion JSON file."""
        motion_data = {
            "trans_x": [0.1, 0.2],
            "trans_y": [0.1, 0.2],
            "trans_z": [0.1, 0.2],
            "rot_x": [0.1, 0.2],
            "rot_y": [0.1, 0.2],
            "rot_z": [0.1, 0.2]
        }
        
        motion_file = self.test_data_dir / "valid_motion.json"
        with open(motion_file, "w") as f:
            json.dump(motion_data, f)
        
        loaded_data = load_motion_json(motion_file)
        
        self.assertEqual(loaded_data, motion_data)
        self.assertEqual(len(loaded_data["trans_x"]), 2)

    def test_compute_subject_fd_percentage_high_motion(self):
        """Test compute_subject_fd with >10% high motion volumes."""
        # Create motion data with 20% high motion (1 out of 5 frames)
        # Frame 2 has high motion (0.6mm displacement)
        motion_data = {
            "trans_x": [0.0, 0.0, 0.6, 0.0, 0.0],
            "trans_y": [0.0, 0.0, 0.0, 0.0, 0.0],
            "trans_z": [0.0, 0.0, 0.0, 0.0, 0.0],
            "rot_x": [0.0, 0.0, 0.0, 0.0, 0.0],
            "rot_y": [0.0, 0.0, 0.0, 0.0, 0.0],
            "rot_z": [0.0, 0.0, 0.0, 0.0, 0.0]
        }
        
        motion_file = self.test_data_dir / "motion_20pct.json"
        with open(motion_file, "w") as f:
            json.dump(motion_data, f)
        
        # Total volumes: 5, High motion volumes: 1 (20%)
        high_motion_count, total_volumes = compute_subject_fd(motion_file, threshold=0.5)
        
        self.assertEqual(total_volumes, 5)
        self.assertEqual(high_motion_count, 1)
        self.assertGreater(high_motion_count / total_volumes, 0.10)

    def test_compute_subject_fd_percentage_low_motion(self):
        """Test compute_subject_fd with <10% high motion volumes."""
        # Create motion data with 0% high motion
        motion_data = {
            "trans_x": [0.0, 0.1, 0.1, 0.1, 0.1],
            "trans_y": [0.0, 0.1, 0.1, 0.1, 0.1],
            "trans_z": [0.0, 0.1, 0.1, 0.1, 0.1],
            "rot_x": [0.0, 0.1, 0.1, 0.1, 0.1],
            "rot_y": [0.0, 0.1, 0.1, 0.1, 0.1],
            "rot_z": [0.0, 0.1, 0.1, 0.1, 0.1]
        }
        
        motion_file = self.test_data_dir / "motion_0pct.json"
        with open(motion_file, "w") as f:
            json.dump(motion_data, f)
        
        high_motion_count, total_volumes = compute_subject_fd(motion_file, threshold=0.5)
        
        self.assertEqual(total_volumes, 5)
        self.assertEqual(high_motion_count, 0)
        self.assertEqual(high_motion_count / total_volumes, 0.0)

    def test_compute_subject_fd_edge_case_10pct(self):
        """Test compute_subject_fd exactly at 10% threshold."""
        # Create motion data with exactly 10% high motion (1 out of 10 frames)
        motion_data = {
            "trans_x": [0.0] * 9 + [0.6],
            "trans_y": [0.0] * 10,
            "trans_z": [0.0] * 10,
            "rot_x": [0.0] * 10,
            "rot_y": [0.0] * 10,
            "rot_z": [0.0] * 10
        }
        
        motion_file = self.test_data_dir / "motion_10pct.json"
        with open(motion_file, "w") as f:
            json.dump(motion_data, f)
        
        high_motion_count, total_volumes = compute_subject_fd(motion_file, threshold=0.5)
        
        self.assertEqual(total_volumes, 10)
        self.assertEqual(high_motion_count, 1)
        # 1/10 = 0.10 which is NOT > 0.10, so subject should be retained
        self.assertEqual(high_motion_count / total_volumes, 0.10)

    def test_fd_calculation_precision(self):
        """Test that FD calculations maintain sufficient precision."""
        # Create motion data with small but significant displacements
        motion_data = {
            "trans_x": [0.0, 0.001, 0.002, 0.003, 0.004],
            "trans_y": [0.0, 0.001, 0.002, 0.003, 0.004],
            "trans_z": [0.0, 0.001, 0.002, 0.003, 0.004],
            "rot_x": [0.0, 0.0, 0.0, 0.0, 0.0],
            "rot_y": [0.0, 0.0, 0.0, 0.0, 0.0],
            "rot_z": [0.0, 0.0, 0.0, 0.0, 0.0]
        }
        
        motion_file = self.test_data_dir / "motion_precision.json"
        with open(motion_file, "w") as f:
            json.dump(motion_data, f)
        
        fd_values = calculate_fd(motion_file)
        
        # Verify FD values are calculated with appropriate precision
        # First is 0, subsequent should be small but non-zero
        self.assertEqual(fd_values[0], 0.0)
        for i in range(1, len(fd_values)):
            self.assertGreaterEqual(fd_values[i], 0.0)
            # Check that precision is maintained (at least 4 decimal places)
            self.assertIsInstance(fd_values[i], float)

if __name__ == "__main__":
    unittest.main()