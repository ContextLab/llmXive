import os
import sys
import json
import csv
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import logging

# Add code directory to path
sys.path.insert(0, 'code')

from preprocess import halt_on_zero_effective_subjects, load_motion_exclusion_log, main

class TestPreprocessHaltLogic(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.data_processed = Path("data/processed")
        self.motion_log_path = self.data_processed / "motion_exclusion_log.csv"
        self.error_log_path = self.data_processed / "motion_exclusion.log"
        
        # Ensure directory exists
        self.data_processed.mkdir(parents=True, exist_ok=True)
        
        # Clean up logs before each test
        if self.error_log_path.exists():
            self.error_log_path.unlink()
        if self.motion_log_path.exists():
            self.motion_log_path.unlink()

    def tearDown(self):
        """Clean up after tests."""
        if self.error_log_path.exists():
            self.error_log_path.unlink()
        if self.motion_log_path.exists():
            self.motion_log_path.unlink()

    def test_halt_on_zero_effective_subjects_writes_log_and_raises(self):
        """
        Test that halt_on_zero_effective_subjects writes the error log with the correct prefix
        and raises a RuntimeError when the effective subjects list is empty.
        """
        # Prepare empty list
        effective_subjects = []
        
        # Verify log does not exist yet
        self.assertFalse(self.error_log_path.exists())

        # Call the function
        with self.assertRaises(RuntimeError) as context:
            halt_on_zero_effective_subjects(effective_subjects)

        # Verify exception message
        self.assertEqual(str(context.exception), "No valid subjects remaining after motion exclusion")

        # Verify log file was created
        self.assertTrue(self.error_log_path.exists())

        # Verify log content contains the required prefix
        with open(self.error_log_path, 'r') as f:
            content = f.read()
            self.assertIn("[MOTION_EXCLUSION_ERROR]", content)
            self.assertIn("No valid subjects remaining after motion exclusion", content)

    def test_no_halt_when_subjects_exist(self):
        """
        Test that the function does not raise an error if effective subjects exist.
        """
        effective_subjects = [{"id": "sub-01", "score": 100.0}]
        
        # Should not raise
        try:
            halt_on_zero_effective_subjects(effective_subjects)
        except RuntimeError:
            self.fail("halt_on_zero_effective_subjects raised RuntimeError unexpectedly")

        # Log should NOT be created
        self.assertFalse(self.error_log_path.exists())

    @patch('preprocess.load_motion_exclusion_log')
    def test_main_halts_when_all_excluded(self, mock_load_motion):
        """
        Integration-style test: Simulate a scenario where T018a excluded ALL subjects.
        Verify that main() triggers the halt logic and writes the error log.
        """
        # Mock valid subjects from T015
        mock_valid_data = {
            "subjects": [
                {"id": "sub-01", "score": 100.0},
                {"id": "sub-02", "score": 110.0}
            ]
        }
        
        # Mock motion log where ALL are excluded
        mock_motion_log = [
            {"subject_id": "sub-01", "translation_mm": 5.0, "rotation_mm": 3.0, "excluded": True},
            {"subject_id": "sub-02", "translation_mm": 4.0, "rotation_mm": 2.5, "excluded": True}
        ]
        
        mock_load_motion.return_value = mock_motion_log

        # Mock the file reading for valid_subjects.json
        with patch('builtins.open', unittest.mock.mock_open(read_data=json.dumps(mock_valid_data))):
            with patch('pathlib.Path.exists', return_value=True): # valid_subjects.json exists
                with self.assertRaises(RuntimeError) as context:
                    main()

        self.assertEqual(str(context.exception), "No valid subjects remaining after motion exclusion")
        self.assertTrue(self.error_log_path.exists())
        with open(self.error_log_path, 'r') as f:
            self.assertIn("[MOTION_EXCLUSION_ERROR]", f.read())

if __name__ == '__main__':
    unittest.main()