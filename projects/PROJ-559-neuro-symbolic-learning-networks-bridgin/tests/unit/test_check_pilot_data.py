"""
Unit tests for code/download/check_pilot_data.py
"""
import os
import sys
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd

# Add the project root to the path so we can import the module
# Assuming this test file is run from the project root or via pytest discovery
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from download.check_pilot_data import check_pilot_data, main

class TestCheckPilotData(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.valid_csv_path = os.path.join(self.temp_dir, "valid_data.csv")
        self.small_csv_path = os.path.join(self.temp_dir, "small_data.csv")
        self.empty_csv_path = os.path.join(self.temp_dir, "empty_data.csv")
        self.malformed_csv_path = os.path.join(self.temp_dir, "malformed_data.csv")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def _create_csv(self, path, rows):
        """Helper to create a CSV file with a given number of data rows."""
        df = pd.DataFrame({
            'id': range(1, rows + 1),
            'problem_id': ['p1'] * rows,
            'correct': [1] * rows,
            'rt_seconds': [1.5] * rows
        })
        df.to_csv(path, index=False)

    def test_valid_data_returns_true(self):
        """Test that valid data (>= 50 rows) returns True."""
        self._create_csv(self.valid_csv_path, 50)
        result = check_pilot_data(self.valid_csv_path)
        self.assertTrue(result)

    def test_valid_data_excess_returns_true(self):
        """Test that valid data (> 50 rows) returns True."""
        self._create_csv(self.valid_csv_path, 100)
        result = check_pilot_data(self.valid_csv_path)
        self.assertTrue(result)

    def test_small_data_returns_false(self):
        """Test that data with < 50 rows returns False."""
        self._create_csv(self.small_csv_path, 49)
        result = check_pilot_data(self.small_csv_path)
        self.assertFalse(result)

    def test_missing_file_returns_false(self):
        """Test that a missing file returns False."""
        missing_path = os.path.join(self.temp_dir, "non_existent.csv")
        result = check_pilot_data(missing_path)
        self.assertFalse(result)

    def test_empty_file_returns_false(self):
        """Test that an empty file returns False."""
        # Create an empty file
        open(self.empty_csv_path, 'w').close()
        result = check_pilot_data(self.empty_csv_path)
        self.assertFalse(result)

    def test_malformed_csv_returns_false(self):
        """Test that a malformed CSV returns False."""
        with open(self.malformed_csv_path, 'w') as f:
            f.write("id,problem_id\n1,p1\n2\n3,p3") # Missing value in row 2
        
        result = check_pilot_data(self.malformed_csv_path)
        # Depending on pandas behavior, this might raise or return partial.
        # The function should catch the exception and return False.
        self.assertFalse(result)

    def test_main_output_format_valid(self):
        """Test that main() prints valid JSON with the correct key."""
        self._create_csv(self.valid_csv_path, 50)
        
        with patch('sys.stdout', new_callable=MagicMock) as mock_stdout:
            with patch('sys.argv', ['check_pilot_data.py', '--data-path', self.valid_csv_path]):
                main()
            
            # Capture the printed output
            call_args = mock_stdout.write.call_args
            output_str = call_args[0][0]
            
            try:
                data = json.loads(output_str)
                self.assertIn('has_human_data', data)
                self.assertTrue(data['has_human_data'])
            except json.JSONDecodeError:
                self.fail("main() did not print valid JSON")

    def test_main_output_format_missing(self):
        """Test that main() prints valid JSON with has_human_data=False for missing file."""
        missing_path = os.path.join(self.temp_dir, "non_existent.csv")
        
        with patch('sys.stdout', new_callable=MagicMock) as mock_stdout:
            with patch('sys.argv', ['check_pilot_data.py', '--data-path', missing_path]):
                main()
            
            call_args = mock_stdout.write.call_args
            output_str = call_args[0][0]
            
            try:
                data = json.loads(output_str)
                self.assertIn('has_human_data', data)
                self.assertFalse(data['has_human_data'])
            except json.JSONDecodeError:
                self.fail("main() did not print valid JSON")

if __name__ == '__main__':
    unittest.main()