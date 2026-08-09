"""
Unit tests for T024f: Normalize Tabular Features Pipeline
"""
import unittest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json
import tempfile
import shutil

# Add code directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from utils.feature_engineering import normalize_features, save_normalization_metadata, load_normalization_metadata

class TestNormalizeFeatures(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_zscore_normalization(self):
        """Test that z-score normalization results in mean ~0 and std ~1"""
        data = {
            'feature1': [10.0, 20.0, 30.0, 40.0, 50.0],
            'feature2': [100.0, 100.0, 100.0, 100.0, 100.0], # Zero variance
            'dataset_id': ['A', 'A', 'A', 'A', 'A']
        }
        df = pd.DataFrame(data)
        
        normalized_df, metadata = normalize_features(df, method="zscore")
        
        # Check feature1
        mean1 = normalized_df['feature1'].mean()
        std1 = normalized_df['feature1'].std()
        
        self.assertAlmostEqual(mean1, 0.0, places=5)
        self.assertAlmostEqual(std1, 1.0, places=5)
        
        # Check feature2 (zero variance case)
        # The function should handle this by setting std=1.0 and keeping values as mean
        # So the normalized values should be 0.0 (since (mean - mean) / 1.0 = 0)
        # Wait, the logic in feature_engineering.py:
        # if std_val == 0: std_val = 1.0; normalized = (col_data - mean) / 1.0
        # So if all values are 100, mean is 100. (100 - 100) / 1 = 0.
        self.assertTrue((normalized_df['feature2'] == 0.0).all())
        self.assertIn('feature2', metadata)
        self.assertEqual(metadata['feature2']['std'], 1.0)

    def test_mean_imputation(self):
        """Test that missing values are imputed with the mean"""
        data = {
            'feature1': [10.0, np.nan, 30.0, 40.0, 50.0],
            'dataset_id': ['A', 'A', 'A', 'A', 'A']
        }
        df = pd.DataFrame(data)
        
        normalized_df, metadata = normalize_features(df, method="zscore")
        
        # The mean of [10, 30, 40, 50] is 32.5
        # The missing value should be filled with 32.5 before normalization
        # So the normalized value for the missing slot should be (32.5 - 32.5) / std = 0.0
        self.assertTrue(np.isclose(normalized_df['feature1'].iloc[1], 0.0, atol=1e-5))

    def test_minmax_normalization(self):
        """Test min-max normalization results in range [0, 1]"""
        data = {
            'feature1': [10.0, 20.0, 30.0, 40.0, 50.0],
            'dataset_id': ['A', 'A', 'A', 'A', 'A']
        }
        df = pd.DataFrame(data)
        
        normalized_df, metadata = normalize_features(df, method="minmax")
        
        self.assertAlmostEqual(normalized_df['feature1'].min(), 0.0, places=5)
        self.assertAlmostEqual(normalized_df['feature1'].max(), 1.0, places=5)
        self.assertIn('min', metadata['feature1'])
        self.assertIn('max', metadata['feature1'])

    def test_empty_dataframe(self):
        """Test handling of empty dataframe"""
        df = pd.DataFrame()
        normalized_df, metadata = normalize_features(df, method="zscore")
        self.assertTrue(normalized_df.empty)
        self.assertEqual(metadata, {})

    def test_metadata_serialization(self):
        """Test that metadata can be saved and loaded correctly"""
        data = {'feature1': [1.0, 2.0, 3.0]}
        df = pd.DataFrame(data)
        
        _, metadata = normalize_features(df, method="zscore")
        
        path = Path(self.test_dir) / "meta.json"
        save_normalization_metadata(metadata, path)
        
        loaded_metadata = load_normalization_metadata(path)
        self.assertEqual(metadata, loaded_metadata)

if __name__ == '__main__':
    unittest.main()