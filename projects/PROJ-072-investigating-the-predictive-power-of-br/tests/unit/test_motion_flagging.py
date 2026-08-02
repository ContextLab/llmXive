import os
import sys
import unittest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import csv

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from preprocessing.motion_flagging import (
    calculate_max_displacement,
    flag_subject_motion,
    run_motion_flagging_pipeline,
    MOTION_THRESHOLD_MM
)

class TestMotionFlagging(unittest.TestCase):

    def test_calculate_max_displacement_translation_only(self):
        """Test max displacement calculation with only translation data."""
        params = {
            "trans_x": np.array([0.0, 1.0, 2.0]),
            "trans_y": np.array([0.0, 0.0, 0.0]),
            "trans_z": np.array([0.0, 0.0, 0.0]),
            "rot_x": np.array([0.0]),
            "rot_y": np.array([0.0]),
            "rot_z": np.array([0.0])
        }
        # Max trans is 2.0. Rot is 0. Max should be 2.0
        # Note: The implementation handles different array lengths by concatenating.
        # If arrays are different lengths, numpy will fail. We assume consistent lengths.
        # Let's fix the test data to be consistent
        params = {
            "trans_x": np.array([0.0, 1.0, 2.0]),
            "trans_y": np.array([0.0, 0.0, 0.0]),
            "trans_z": np.array([0.0, 0.0, 0.0]),
            "rot_x": np.array([0.0, 0.0, 0.0]),
            "rot_y": np.array([0.0, 0.0, 0.0]),
            "rot_z": np.array([0.0, 0.0, 0.0])
        }
        result = calculate_max_displacement(params)
        self.assertEqual(result, 2.0)

    def test_calculate_max_displacement_rotation_contribution(self):
        """Test that rotation contributes to max displacement when converted to mm."""
        # 1 radian rotation * 60mm radius = 60mm displacement
        params = {
            "trans_x": np.array([0.0, 0.0, 0.0]),
            "trans_y": np.array([0.0, 0.0, 0.0]),
            "trans_z": np.array([0.0, 0.0, 0.0]),
            "rot_x": np.array([1.0, 1.0, 1.0]), # 1 radian
            "rot_y": np.array([0.0, 0.0, 0.0]),
            "rot_z": np.array([0.0, 0.0, 0.0])
        }
        result = calculate_max_displacement(params)
        # Should be 60.0 (1.0 * 60)
        self.assertEqual(result, 60.0)

    def test_flag_subject_motion_pass(self):
        """Test flagging a subject with motion under threshold."""
        # Mock the load_motion_parameters function
        mock_params = {
            "trans_x": np.array([0.0, 0.1, 0.2]),
            "trans_y": np.array([0.0, 0.1, 0.2]),
            "trans_z": np.array([0.0, 0.1, 0.2]),
            "rot_x": np.array([0.0, 0.0, 0.0]),
            "rot_y": np.array([0.0, 0.0, 0.0]),
            "rot_z": np.array([0.0, 0.0, 0.0])
        }
        
        with patch('preprocessing.motion_flagging.load_motion_parameters', return_value=mock_params):
            result = flag_subject_motion("sub-01")
            
        self.assertTrue(result["included"])
        self.assertEqual(result["reason"], "Pass")
        self.assertLess(result["max_displacement"], MOTION_THRESHOLD_MM)

    def test_flag_subject_motion_fail(self):
        """Test flagging a subject with motion over threshold."""
        mock_params = {
            "trans_x": np.array([0.0, 3.0, 0.0]), # 3mm > 2mm
            "trans_y": np.array([0.0, 0.0, 0.0]),
            "trans_z": np.array([0.0, 0.0, 0.0]),
            "rot_x": np.array([0.0, 0.0, 0.0]),
            "rot_y": np.array([0.0, 0.0, 0.0]),
            "rot_z": np.array([0.0, 0.0, 0.0])
        }
        
        with patch('preprocessing.motion_flagging.load_motion_parameters', return_value=mock_params):
            result = flag_subject_motion("sub-02")
            
        self.assertFalse(result["included"])
        self.assertIn("Exceeds threshold", result["reason"])
        self.assertGreater(result["max_displacement"], MOTION_THRESHOLD_MM)

    def test_flag_subject_motion_error(self):
        """Test flagging a subject where loading parameters fails."""
        with patch('preprocessing.motion_flagging.load_motion_parameters', side_effect=FileNotFoundError("Missing file")):
            result = flag_subject_motion("sub-03")
            
        self.assertFalse(result["included"])
        self.assertIn("Error loading parameters", result["reason"])
        self.assertTrue(np.isnan(result["max_displacement"]))

if __name__ == '__main__':
    unittest.main()