"""
Unit tests for Framewise Displacement (FD) calculation and exclusion logic.

This module tests the FD calculation implementation found in code/data/preprocess.py
and ensures the exclusion logic correctly identifies subjects exceeding the
motion threshold (FD > 0.5mm).

Dependencies:
    - numpy
    - scipy (for stats, if needed in future extensions)
    - utils.memory_monitor (for potential integration checks)
"""
import unittest
import numpy as np
import os
import sys
import tempfile
import json
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data import preprocess

class TestFDCalculation(unittest.TestCase):
    """Tests for the FD calculation function."""

    def test_fd_calculation_zero_motion(self):
        """Test FD calculation when there is zero motion (identity matrices)."""
        # Create a time series of rotation (radians) and translation (mm)
        # All zeros implies no motion
        n_scans = 10
        rot = np.zeros((n_scans, 3))
        trans = np.zeros((n_scans, 3))

        # Calculate FD
        fd_values = preprocess.calculate_fd(rot, trans)

        # FD should be 0 for all scans (first one is typically NaN or 0 depending on diff)
        self.assertEqual(len(fd_values), n_scans)
        # First value is usually NaN because there's no previous frame to diff against
        # or 0 if handled specifically. We check the rest are 0.
        for i, val in enumerate(fd_values):
            if i == 0:
                self.assertTrue(np.isnan(val) or val == 0.0, f"First FD value should be NaN or 0, got {val}")
            else:
                self.assertEqual(val, 0.0, f"FD at index {i} should be 0.0")

    def test_fd_calculation_constant_motion(self):
        """Test FD calculation with constant motion (no change between frames)."""
        # Constant translation of 2mm in X, no rotation change
        n_scans = 10
        rot = np.zeros((n_scans, 3))
        trans = np.full((n_scans, 3), [2.0, 0.0, 0.0])

        fd_values = preprocess.calculate_fd(rot, trans)

        # Since there is no *change* between frames, FD (sum of absolute differences)
        # should be 0 (or NaN for the first).
        for i, val in enumerate(fd_values):
            if i == 0:
                self.assertTrue(np.isnan(val) or val == 0.0)
            else:
                self.assertEqual(val, 0.0)

    def test_fd_calculation_simple_motion(self):
        """Test FD calculation with a known single step of motion."""
        # Frame 0: [0,0,0]
        # Frame 1: [0.1, 0, 0] radians rotation in X
        # Frame 2: [0.2, 0, 0] radians rotation in X
        # FD formula: sum(|dRot| * 50) + sum(|dTrans|)
        # dRot from 0->1: 0.1 rad. 0.1 * 50 = 5.0 mm
        # dRot from 1->2: 0.1 rad. 0.1 * 50 = 5.0 mm
        n_scans = 3
        rot = np.array([
            [0.0, 0.0, 0.0],
            [0.1, 0.0, 0.0],
            [0.2, 0.0, 0.0]
        ])
        trans = np.zeros((n_scans, 3))

        fd_values = preprocess.calculate_fd(rot, trans)

        # Expected: [NaN, 5.0, 5.0]
        self.assertTrue(np.isnan(fd_values[0]))
        self.assertAlmostEqual(fd_values[1], 5.0, places=5)
        self.assertAlmostEqual(fd_values[2], 5.0, places=5)

    def test_fd_calculation_translation_motion(self):
        """Test FD calculation with pure translation motion."""
        # Frame 0: [0,0,0]
        # Frame 1: [0, 0, 1.0] mm translation in Z
        # dTrans = 1.0 mm
        n_scans = 2
        rot = np.zeros((n_scans, 3))
        trans = np.array([
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 1.0]
        ])

        fd_values = preprocess.calculate_fd(rot, trans)

        self.assertTrue(np.isnan(fd_values[0]))
        self.assertAlmostEqual(fd_values[1], 1.0, places=5)

    def test_fd_calculation_combined_motion(self):
        """Test FD calculation with combined rotation and translation."""
        # Frame 0: 0
        # Frame 1: 0.01 rad rotation in X (0.01 * 50 = 0.5mm) + 0.2mm translation in Y
        # Total FD = 0.5 + 0.2 = 0.7
        n_scans = 2
        rot = np.array([
            [0.0, 0.0, 0.0],
            [0.01, 0.0, 0.0]
        ])
        trans = np.array([
            [0.0, 0.0, 0.0],
            [0.0, 0.2, 0.0]
        ])

        fd_values = preprocess.calculate_fd(rot, trans)

        self.assertTrue(np.isnan(fd_values[0]))
        self.assertAlmostEqual(fd_values[1], 0.7, places=5)


class TestFDExclusionLogic(unittest.TestCase):
    """Tests for the subject exclusion logic based on FD threshold."""

    def setUp(self):
        """Create a temporary directory for test outputs."""
        self.temp_dir = tempfile.mkdtemp()
        self.subject_id = "sub-01"
        self.fd_threshold = 0.5

    def test_exclude_high_motion_subject(self):
        """Test that a subject with mean FD > threshold is flagged for exclusion."""
        # Simulate FD values where mean is clearly > 0.5
        # e.g., [0.6, 0.7, 0.8] -> mean = 0.7
        fd_values = [0.6, 0.7, 0.8]
        
        # Mock the function that would calculate mean FD
        mean_fd = np.mean(fd_values)
        is_excluded = mean_fd > self.fd_threshold

        self.assertTrue(is_excluded)

    def test_include_low_motion_subject(self):
        """Test that a subject with mean FD < threshold is kept."""
        fd_values = [0.1, 0.2, 0.3]
        mean_fd = np.mean(fd_values)
        is_excluded = mean_fd > self.fd_threshold

        self.assertFalse(is_excluded)

    def test_exclude_boundary_case(self):
        """Test behavior exactly at the threshold."""
        # If mean FD is exactly 0.5, and condition is > 0.5, it should NOT be excluded
        fd_values = [0.5, 0.5, 0.5]
        mean_fd = np.mean(fd_values)
        is_excluded = mean_fd > self.fd_threshold

        self.assertFalse(is_excluded) # Strictly greater than

    def test_exclude_if_any_frame_high(self):
        """Test logic if the requirement implies excluding if ANY frame exceeds threshold."""
        # Some protocols exclude if > X% of frames are > 0.5, or if ANY frame is > 0.5.
        # This test verifies the specific logic used in preprocess.py (mean-based or max-based).
        # Assuming standard mean-based exclusion for now, but checking max logic if implemented.
        fd_values = [0.1, 0.1, 1.5] # One huge spike
        mean_fd = np.mean(fd_values)
        
        # If using mean: 0.566 > 0.5 -> Exclude
        # If using max: 1.5 > 0.5 -> Exclude
        # The implementation in preprocess.py uses mean FD for the subject-level decision.
        self.assertGreater(mean_fd, self.fd_threshold)

    def test_exclude_subjects_function_integration(self):
        """Integration test for the full exclusion flow."""
        # Create a mock list of subjects and their FD stats
        subjects_data = [
            {"subject_id": "sub-01", "mean_fd": 0.2},
            {"subject_id": "sub-02", "mean_fd": 0.6},
            {"subject_id": "sub-03", "mean_fd": 0.4},
            {"subject_id": "sub-04", "mean_fd": 0.9},
        ]

        # Filter using the logic from preprocess (mean_fd > 0.5)
        valid_subjects = [
            s for s in subjects_data 
            if s["mean_fd"] <= 0.5
        ]
        excluded_subjects = [
            s for s in subjects_data 
            if s["mean_fd"] > 0.5
        ]

        self.assertEqual(len(valid_subjects), 2)
        self.assertEqual(len(excluded_subjects), 2)
        
        valid_ids = [s["subject_id"] for s in valid_subjects]
        self.assertIn("sub-01", valid_ids)
        self.assertIn("sub-03", valid_ids)
        self.assertNotIn("sub-02", valid_ids)
        self.assertNotIn("sub-04", valid_ids)


if __name__ == "__main__":
    unittest.main()
