"""
Unit tests for code/preprocessing/load_data.py
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from preprocessing.load_data import (
    normalize_columns,
    save_to_csv,
    TARGET_COLUMNS,
    REQUIRED_RAW_COLUMNS
)

class TestLoadData(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.output_path = Path(self.test_dir) / "test_output.csv"

    def tearDown(self):
        """Clean up test files."""
        if self.output_path.exists():
            self.output_path.unlink()

    def test_normalize_columns_standard(self):
        """Test normalization with standard column names."""
        data = {
            'timestamp': [1.0, 2.0, 3.0],
            'x': [10.0, 20.0, 30.0],
            'y': [5.0, 15.0, 25.0],
            'pupil_diameter': [4.0, 4.1, 3.9]
        }
        df = pd.DataFrame(data)
        result = normalize_columns(df)
        
        self.assertEqual(list(result.columns), TARGET_COLUMNS)
        self.assertEqual(len(result), 3)

    def test_normalize_columns_alternative_names(self):
        """Test normalization with alternative column names."""
        data = {
            'time': [1.0, 2.0, 3.0],
            'x_pos': [10.0, 20.0, 30.0],
            'y_pos': [5.0, 15.0, 25.0],
            'pupil_size': [4.0, 4.1, 3.9]
        }
        df = pd.DataFrame(data)
        result = normalize_columns(df)
        
        self.assertEqual(list(result.columns), TARGET_COLUMNS)
        # Verify values are preserved
        np.testing.assert_array_equal(result['timestamp'], data['time'])
        np.testing.assert_array_equal(result['pupil_diameter'], data['pupil_size'])

    def test_normalize_columns_nan_handling(self):
        """Test that rows with NaN in critical columns are dropped."""
        data = {
            'timestamp': [1.0, np.nan, 3.0],
            'x': [10.0, 20.0, 30.0],
            'y': [5.0, 15.0, np.nan],
            'pupil_diameter': [4.0, 4.1, 3.9]
        }
        df = pd.DataFrame(data)
        result = normalize_columns(df)
        
        # Row 1 has NaN in timestamp, Row 2 has NaN in y
        # Both should be dropped.
        self.assertEqual(len(result), 0)

    def test_save_to_csv(self):
        """Test saving DataFrame to CSV."""
        data = {
            'timestamp': [1.0, 2.0],
            'x': [10.0, 20.0],
            'y': [5.0, 15.0],
            'pupil_diameter': [4.0, 4.1]
        }
        df = pd.DataFrame(data)
        
        save_to_csv(df, self.output_path)
        
        self.assertTrue(self.output_path.exists())
        
        # Read back and verify
        loaded_df = pd.read_csv(self.output_path)
        self.assertEqual(list(loaded_df.columns), TARGET_COLUMNS)
        np.testing.assert_array_equal(loaded_df['timestamp'], df['timestamp'])

    def test_normalize_columns_missing_required(self):
        """Test that normalization raises error if required columns are missing."""
        data = {
            'timestamp': [1.0, 2.0],
            'x': [10.0, 20.0],
            # Missing y and pupil_diameter
        }
        df = pd.DataFrame(data)
        
        with self.assertRaises(ValueError):
            normalize_columns(df)

if __name__ == '__main__':
    unittest.main()