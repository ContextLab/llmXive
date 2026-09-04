import unittest
import os
import sys
import tempfile
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from data.save_aligned_data import (
    calculate_completeness,
    validate_data_length,
    calculate_md5,
    MIN_COMPLETENESS,
    MIN_DATA_LENGTH
)

class TestSaveAlignedData(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
        
        # Create a sample DataFrame for testing
        dates = pd.date_range(start='2020-01-01', periods=30, freq='D')
        self.df_complete = pd.DataFrame({
            'date': dates.strftime('%Y-%m-%d'),
            'news_zscore': np.random.randn(30),
            'anxiety_zscore': np.random.randn(30)
        })
        
        # DataFrame with missing values (but > 95% completeness)
        self.df_partial = self.df_complete.copy()
        self.df_partial.loc[0:1, 'news_zscore'] = np.nan  # 2 missing out of 30 = 93.3%
        
        # DataFrame with too many missing values (< 95% completeness)
        self.df_sparse = self.df_complete.copy()
        self.df_sparse.loc[0:5, 'news_zscore'] = np.nan  # 6 missing out of 30 = 80%
        
        # DataFrame with insufficient length
        self.df_short = pd.DataFrame({
            'date': pd.date_range(start='2020-01-01', periods=15, freq='D').strftime('%Y-%m-%d'),
            'news_zscore': np.random.randn(15),
            'anxiety_zscore': np.random.randn(15)
        })
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_calculate_completeness_full_data(self):
        """Test completeness calculation with no missing values."""
        completeness = calculate_completeness(self.df_complete)
        self.assertEqual(completeness, 1.0)
    
    def test_calculate_completeness_partial_data(self):
        """Test completeness calculation with some missing values."""
        # 2 missing out of 30 rows -> 28/30 = 0.9333
        completeness = calculate_completeness(self.df_partial)
        expected = 28 / 30
        self.assertAlmostEqual(completeness, expected, places=4)
    
    def test_calculate_completeness_sparse_data(self):
        """Test completeness calculation with many missing values."""
        # 6 missing out of 30 rows -> 24/30 = 0.8
        completeness = calculate_completeness(self.df_sparse)
        expected = 24 / 30
        self.assertAlmostEqual(completeness, expected, places=4)
    
    def test_validate_data_length_sufficient(self):
        """Test data length validation with sufficient rows."""
        result = validate_data_length(self.df_complete)
        self.assertTrue(result)
    
    def test_validate_data_length_insufficient(self):
        """Test data length validation with insufficient rows."""
        result = validate_data_length(self.df_short)
        self.assertFalse(result)
    
    def test_validate_data_length_boundary(self):
        """Test data length validation at boundary (exactly 20 rows)."""
        df_boundary = pd.DataFrame({
            'date': pd.date_range(start='2020-01-01', periods=20, freq='D').strftime('%Y-%m-%d'),
            'news_zscore': np.random.randn(20),
            'anxiety_zscore': np.random.randn(20)
        })
        result = validate_data_length(df_boundary)
        self.assertTrue(result)
    
    def test_calculate_md5(self):
        """Test MD5 checksum calculation."""
        test_file = self.test_dir / "test_checksum.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        checksum = calculate_md5(test_file)
        # Known MD5 for "Hello, World!"
        expected = "65a8e27d8879283831b664bd8b7f0ad4"
        self.assertEqual(checksum, expected)
    
    def test_empty_dataframe_completeness(self):
        """Test completeness calculation with empty DataFrame."""
        empty_df = pd.DataFrame(columns=['date', 'news_zscore', 'anxiety_zscore'])
        completeness = calculate_completeness(empty_df)
        self.assertEqual(completeness, 0.0)

if __name__ == '__main__':
    unittest.main()