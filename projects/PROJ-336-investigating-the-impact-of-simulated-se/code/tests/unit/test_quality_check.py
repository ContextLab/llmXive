"""
Unit tests for the quality check module.
"""
import unittest
import json
import tempfile
import os
from pathlib import Path
import sys
import numpy as np

# Add code to path if running standalone
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.data.quality_check import calculate_fd, compute_subject_fd, load_motion_json


class TestQualityCheck(unittest.TestCase):

    def setUp(self):
        """Set up temporary directory for test files."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.json_file = self.temp_dir / "test_motion.json"

    def tearDown(self):
        """Clean up temporary directory."""
        if self.json_file.exists():
            self.json_file.unlink()
        self.temp_dir.rmdir()

    def test_calculate_fd_basic(self):
        """Test basic FD calculation with known values."""
        # Create a simple motion array: [rot_x, rot_y, rot_z, trans_x, trans_y, trans_z]
        # 2 timepoints, so 1 FD value
        motion = np.array([
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.1, 0.0, 0.0]
        ])
        
        # Expected FD: |0.1| (trans_x diff) = 0.1
        # Rotations are 0, so no contribution
        fd = calculate_fd(motion)
        
        self.assertEqual(len(fd), 1)
        self.assertAlmostEqual(fd[0], 0.1, places=5)

    def test_calculate_fd_rotation(self):
        """Test FD calculation with rotation changes."""
        # 2 timepoints
        # rot_x changes by 0.01 radians
        # radius = 50mm -> displacement = 0.01 * 50 = 0.5mm
        motion = np.array([
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.01, 0.0, 0.0, 0.0, 0.0, 0.0]
        ])
        
        fd = calculate_fd(motion)
        # Expected: 0.01 * 50 = 0.5
        self.assertAlmostEqual(fd[0], 0.5, places=5)

    def test_calculate_fd_combined(self):
        """Test FD calculation with combined translation and rotation."""
        # 2 timepoints
        # trans_x diff = 0.1
        # rot_x diff = 0.01 (0.5mm)
        motion = np.array([
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.01, 0.0, 0.0, 0.1, 0.0, 0.0]
        ])
        
        fd = calculate_fd(motion)
        # Expected: 0.5 (rot) + 0.1 (trans) = 0.6
        self.assertAlmostEqual(fd[0], 0.6, places=5)

    def test_calculate_fd_invalid_shape(self):
        """Test that invalid motion shape raises error."""
        motion = np.array([[0.0, 0.0, 0.0]]) # Only 3 params
        with self.assertRaises(ValueError):
            calculate_fd(motion)

    def test_calculate_fd_multiple_timepoints(self):
        """Test FD calculation with multiple timepoints."""
        # 3 timepoints -> 2 FD values
        motion = np.array([
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.1, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.2, 0.0, 0.0]
        ])
        
        fd = calculate_fd(motion)
        self.assertEqual(len(fd), 2)
        self.assertAlmostEqual(fd[0], 0.1, places=5)
        self.assertAlmostEqual(fd[1], 0.1, places=5)

    def test_compute_subject_fd_integration(self):
        """Test full computation from JSON file."""
        # Create mock JSON data matching OpenNeuro format
        # 5 timepoints
        n_timepoints = 5
        data = {
            "trans_x": [0.0, 0.1, 0.2, 0.1, 0.0],
            "trans_y": [0.0, 0.0, 0.0, 0.0, 0.0],
            "trans_z": [0.0, 0.0, 0.0, 0.0, 0.0],
            "rot_x": [0.0, 0.0, 0.0, 0.0, 0.0],
            "rot_y": [0.0, 0.0, 0.0, 0.0, 0.0],
            "rot_z": [0.0, 0.0, 0.0, 0.0, 0.0]
        }
        
        with open(self.json_file, 'w') as f:
            json.dump(data, f)
        
        sub_id, mean_fd, max_fd, fd_vals = compute_subject_fd(self.json_file)
        
        # Expected FDs:
        # t0->t1: |0.1| = 0.1
        # t1->t2: |0.1| = 0.1
        # t2->t3: |-0.1| = 0.1
        # t3->t4: |-0.1| = 0.1
        expected_fds = [0.1, 0.1, 0.1, 0.1]
        
        self.assertEqual(len(fd_vals), 4)
        for i, val in enumerate(fd_vals):
            self.assertAlmostEqual(val, expected_fds[i], places=5)
        
        self.assertAlmostEqual(mean_fd, 0.1, places=5)
        self.assertAlmostEqual(max_fd, 0.1, places=5)
        self.assertEqual(sub_id, self.json_file.parent.name)

    def test_compute_subject_fd_missing_keys(self):
        """Test that missing motion keys raise an error."""
        data = {
            "other_key": [1, 2, 3]
        }
        
        with open(self.json_file, 'w') as f:
            json.dump(data, f)
        
        with self.assertRaises(ValueError):
            compute_subject_fd(self.json_file)


if __name__ == '__main__':
    unittest.main()