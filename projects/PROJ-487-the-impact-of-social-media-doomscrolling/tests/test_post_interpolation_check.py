import unittest
import sys
import os
import tempfile
import pandas as pd
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data.post_interpolation_check import calculate_completeness, check_post_interpolation_completeness

class TestPostInterpolationCheck(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.input_path = os.path.join(self.temp_dir, "aligned_timeseries.csv")
        self.output_path = os.path.join(self.temp_dir, "validation_status.json")

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_calculate_completeness_perfect(self):
        """Test completeness calculation with no missing values."""
        df = pd.DataFrame({
            'date': ['2023-01-01', '2023-01-02', '2023-01-03'],
            'gdelt': [10.0, 20.0, 30.0],
            'trends': [5.0, 15.0, 25.0]
        })
        completeness = calculate_completeness(df)
        self.assertEqual(completeness, 100.0)

    def test_calculate_completeness_partial(self):
        """Test completeness calculation with some missing values."""
        df = pd.DataFrame({
            'date': ['2023-01-01', '2023-01-02', '2023-01-03'],
            'gdelt': [10.0, None, 30.0],
            'trends': [5.0, 15.0, 25.0]
        })
        # 8 non-null out of 9 total = 88.88...%
        completeness = calculate_completeness(df)
        self.assertAlmostEqual(completeness, 88.888888, places=4)

    def test_calculate_completeness_empty(self):
        """Test completeness calculation with empty DataFrame."""
        df = pd.DataFrame()
        completeness = calculate_completeness(df)
        self.assertEqual(completeness, 0.0)

    def test_check_completeness_passed(self):
        """Test that check passes when completeness >= threshold."""
        df = pd.DataFrame({
            'date': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05'],
            'gdelt': [10.0, 20.0, 30.0, 40.0, 50.0],
            'trends': [5.0, 15.0, 25.0, 35.0, 45.0]
        })
        df.to_csv(self.input_path, index=False)
        
        result = check_post_interpolation_completeness(self.input_path, self.output_path, threshold=95.0)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.output_path))
        
        with open(self.output_path, 'r') as f:
            status = json.load(f)
        
        self.assertEqual(status['status'], 'PASSED')
        self.assertEqual(status['passed'], True)

    def test_check_completeness_failed(self):
        """Test that check fails when completeness < threshold."""
        # Create data with ~50% missing values
        df = pd.DataFrame({
            'date': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05'],
            'gdelt': [10.0, None, 30.0, None, 50.0],
            'trends': [None, 15.0, None, 35.0, None]
        })
        df.to_csv(self.input_path, index=False)
        
        result = check_post_interpolation_completeness(self.input_path, self.output_path, threshold=95.0)
        
        self.assertFalse(result)
        self.assertTrue(os.path.exists(self.output_path))
        
        with open(self.output_path, 'r') as f:
            status = json.load(f)
        
        self.assertEqual(status['status'], 'FAILED')
        self.assertEqual(status['passed'], False)

    def test_check_completeness_file_not_found(self):
        """Test that FileNotFoundError is raised when input file missing."""
        with self.assertRaises(FileNotFoundError):
            check_post_interpolation_completeness(
                os.path.join(self.temp_dir, "nonexistent.csv"),
                self.output_path
            )

    def test_check_completeness_empty_file(self):
        """Test that ValueError is raised when file is empty."""
        # Create empty CSV
        pd.DataFrame().to_csv(self.input_path, index=False)
        
        with self.assertRaises(ValueError):
            check_post_interpolation_completeness(self.input_path, self.output_path)

if __name__ == '__main__':
    unittest.main()