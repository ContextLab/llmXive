"""
Unit tests for the Recruitment Gate (T013a).

Tests the logic that halts study execution if recruited count < 15.
"""
import os
import sys
import json
import tempfile
import shutil
import unittest
from unittest.mock import patch, mock_open
from io import StringIO

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from data_collection import enforce_recruitment_gate, LOGS_FILE, DATA_DIR, load_existing_logs

class TestRecruitmentGate(unittest.TestCase):
    
    def setUp(self):
        """Set up a temporary directory for test data."""
        self.test_dir = tempfile.mkdtemp()
        self.test_data_dir = os.path.join(self.test_dir, "data", "raw")
        os.makedirs(self.test_data_dir, exist_ok=True)
        
        # Patch the global constants to use our temp dir
        self.original_data_dir = DATA_DIR
        self.original_logs_file = LOGS_FILE
        
        # We cannot easily patch module-level constants used in the function 
        # without reloading the module or patching the function's globals.
        # Instead, we will test the logic by manipulating the file system 
        # and using a specific test function that mimics the behavior.
        
        # To properly test, we will re-implement the logic locally or 
        # patch the os.path and open calls.
        
        # Strategy: Patch the file paths used by the functions.
        import data_collection
        data_collection.DATA_DIR = self.test_data_dir
        data_collection.LOGS_FILE = os.path.join(self.test_data_dir, "participant_logs.json")

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
        import data_collection
        data_collection.DATA_DIR = self.original_data_dir
        data_collection.LOGS_FILE = self.original_logs_file

    def test_gate_passes_with_15_participants(self):
        """Test that the gate passes when count is exactly 15."""
        logs_path = os.path.join(self.test_data_dir, "participant_logs.json")
        data = [{"id": str(i)} for i in range(15)]
        with open(logs_path, 'w') as f:
            json.dump(data, f)
        
        # Mock sys.exit to capture the call instead of exiting
        with patch('sys.exit') as mock_exit:
            result = enforce_recruitment_gate()
            mock_exit.assert_not_called()
            self.assertTrue(result)

    def test_gate_passes_with_more_than_15(self):
        """Test that the gate passes when count > 15."""
        logs_path = os.path.join(self.test_data_dir, "participant_logs.json")
        data = [{"id": str(i)} for i in range(20)]
        with open(logs_path, 'w') as f:
            json.dump(data, f)
        
        with patch('sys.exit') as mock_exit:
            result = enforce_recruitment_gate()
            mock_exit.assert_not_called()
            self.assertTrue(result)

    def test_gate_fails_with_less_than_15(self):
        """Test that the gate fails and exits with code 1 when count < 15."""
        logs_path = os.path.join(self.test_data_dir, "participant_logs.json")
        data = [{"id": str(i)} for i in range(10)]
        with open(logs_path, 'w') as f:
            json.dump(data, f)
        
        with patch('sys.exit') as mock_exit:
            with patch('sys.stderr') as mock_stderr:
                # The function calls logger.error which writes to stderr
                # We mainly care that sys.exit(1) is called
                try:
                    enforce_recruitment_gate()
                except SystemExit as e:
                    self.assertEqual(e.code, 1)
                    mock_exit.assert_called_with(1)
                    return
                self.fail("enforce_recruitment_gate() did not raise SystemExit")

    def test_gate_fails_with_empty_logs(self):
        """Test that the gate fails when no logs exist."""
        # Ensure file does not exist
        logs_path = os.path.join(self.test_data_dir, "participant_logs.json")
        if os.path.exists(logs_path):
            os.remove(logs_path)
        
        with self.assertRaises(SystemExit) as context:
            enforce_recruitment_gate()
        
        self.assertEqual(context.exception.code, 1)

    def test_gate_fails_with_14_participants(self):
        """Test boundary condition: 14 participants should fail."""
        logs_path = os.path.join(self.test_data_dir, "participant_logs.json")
        data = [{"id": str(i)} for i in range(14)]
        with open(logs_path, 'w') as f:
            json.dump(data, f)
        
        with self.assertRaises(SystemExit) as context:
            enforce_recruitment_gate()
        
        self.assertEqual(context.exception.code, 1)

if __name__ == '__main__':
    unittest.main()