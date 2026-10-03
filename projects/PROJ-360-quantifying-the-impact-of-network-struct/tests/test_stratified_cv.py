import os
import sys
import unittest
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from stratified_cv import (
    bin_target_for_stratification,
    run_stratified_cv,
    load_filtered_features,
    setup_cv_logger
)

class TestStratifiedCV(unittest.TestCase):

    def setUp(self):
        self.logger = setup_cv_logger()
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_bin_target_for_stratification(self):
        """Test that target binning creates correct number of bins."""
        # Create a large enough dataset to ensure bins
        y = pd.Series(np.random.rand(100))
        bins = bin_target_for_stratification(y, n_bins=5)
        self.assertIsNotNone(bins)
        self.assertEqual(len(bins), 100)
        # Should have at least 2 unique bins
        unique_bins = len(np.unique(bins))
        self.assertGreaterEqual(unique_bins, 2)

    def test_bin_target_fallback_uniform(self):
        """Test fallback to uniform binning when quantile fails."""
        # Create data with very few unique values
        y = pd.Series([1.0, 1.0, 2.0, 2.0, 3.0, 3.0])
        bins = bin_target_for_stratification(y, n_bins=5)
        # Should not crash and return something
        self.assertIsNotNone(bins)

    def test_run_stratified_cv_basic(self):
        """Test basic CV run."""
        # Create dummy data
        X = pd.DataFrame({
            'f1': np.random.rand(50),
            'f2': np.random.rand(50)
        })
        y = pd.Series(np.random.rand(50))
        
        # Mock a simple model
        from sklearn.linear_model import LinearRegression
        model = LinearRegression()
        
        results = run_stratified_cv(model, X, y, k=5, seed=42)
        
        self.assertIn('folds', results)
        self.assertEqual(len(results['folds']), 5)
        self.assertIn('r2_mean', results)
        self.assertIn('r2_std', results)
        self.assertIn('rmse_mean', results)
        self.assertIn('rmse_std', results)

    def test_run_stratified_cv_small_sample(self):
        """Test CV with small sample size (should handle gracefully)."""
        X = pd.DataFrame({
            'f1': [1.0, 2.0, 3.0, 4.0, 5.0]
        })
        y = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        
        from sklearn.linear_model import LinearRegression
        model = LinearRegression()
        
        # Should not crash
        results = run_stratified_cv(model, X, y, k=5, seed=42)
        self.assertIn('folds', results)

    def test_load_filtered_features_missing_file(self):
        """Test loading features when file does not exist."""
        with self.assertRaises(FileNotFoundError):
            load_filtered_features(Path("/nonexistent/path.csv"))

    def test_load_filtered_features_missing_target(self):
        """Test loading features when target column is missing."""
        csv_path = self.temp_path / "test.csv"
        df = pd.DataFrame({'f1': [1, 2, 3], 'f2': [4, 5, 6]})
        df.to_csv(csv_path, index=False)
        
        with self.assertRaises(ValueError):
            load_filtered_features(csv_path)

    def test_load_filtered_features_success(self):
        """Test successful loading of features."""
        csv_path = self.temp_path / "test.csv"
        df = pd.DataFrame({
            'f1': [1.0, 2.0, 3.0, 4.0, 5.0],
            'f2': [2.0, 3.0, 4.0, 5.0, 6.0],
            'thermal_conductivity_scalar': [10.0, 20.0, 30.0, 40.0, 50.0]
        })
        df.to_csv(csv_path, index=False)
        
        X, y = load_filtered_features(csv_path)
        
        self.assertEqual(len(X), 5)
        self.assertEqual(len(y), 5)
        self.assertIn('f1', X.columns)
        self.assertIn('f2', X.columns)
        self.assertTrue(all(y == [10.0, 20.0, 30.0, 40.0, 50.0]))

if __name__ == '__main__':
    unittest.main()