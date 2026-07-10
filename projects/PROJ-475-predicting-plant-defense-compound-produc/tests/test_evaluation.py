"""
Unit tests for the evaluation module (T029: Permutation Test).
"""
import unittest
import tempfile
import os
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add project root to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.evaluation import run_permutation_test, calculate_p_value, save_permutation_results


class TestPermutationTest(unittest.TestCase):
    """Tests for permutation test logic."""

    def setUp(self):
        """Create a small synthetic dataset for testing."""
        np.random.seed(42)
        n_samples = 50
        n_features = 5
        
        # Create features
        X = np.random.randn(n_samples, n_features)
        # Create a target with some signal
        y = X[:, 0] * 2 + X[:, 1] * 0.5 + np.random.randn(n_samples) * 0.1
        
        self.df = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(n_features)])
        self.df['target'] = y
        self.target_col = 'target'
        self.feature_cols = [f'feature_{i}' for i in range(n_features)]

    def test_run_permutation_test_returns_values(self):
        """Test that run_permutation_test returns expected types and values."""
        # Use a small number of permutations for speed in tests
        observed, null_dist, time_taken = run_permutation_test(
            data=self.df,
            target_col=self.target_col,
            feature_cols=self.feature_cols,
            n_permutations=10, # Small number for unit test
            model_type='lasso',
            random_state=42
        )
        
        self.assertIsInstance(observed, float)
        self.assertIsInstance(null_dist, np.ndarray)
        self.assertEqual(len(null_dist), 10)
        self.assertIsInstance(time_taken, float)
        self.assertGreater(time_taken, 0)

    def test_null_distribution_centered_near_zero(self):
        """
        Test that the null distribution of R² scores for shuffled data
        is centered near zero (or negative) since there is no real relationship.
        """
        # Create data with NO relationship
        np.random.seed(42)
        n_samples = 30
        X = np.random.randn(n_samples, 3)
        y = np.random.randn(n_samples) # Random noise
        df_no_signal = pd.DataFrame(X, columns=['f1', 'f2', 'f3'])
        df_no_signal['target'] = y
        
        observed, null_dist, _ = run_permutation_test(
            data=df_no_signal,
            target_col='target',
            feature_cols=['f1', 'f2', 'f3'],
            n_permutations=20,
            model_type='lasso',
            random_state=42
        )
        
        # The mean of the null distribution should be close to 0
        mean_null = np.mean(null_dist)
        self.assertLessEqual(mean_null, 0.2) # Allow some tolerance for small sample size

    def test_calculate_p_value_logic(self):
        """Test p-value calculation logic."""
        observed = 0.8
        null_dist = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        
        p_val = calculate_p_value(observed, null_dist)
        
        # No null scores >= 0.8
        # p = (0 + 1) / (5 + 1) = 1/6
        expected = 1.0 / 6.0
        self.assertAlmostEqual(p_val, expected)

    def test_calculate_p_value_high_observed(self):
        """Test p-value when observed is very high compared to null."""
        observed = 0.9
        null_dist = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        
        p_val = calculate_p_value(observed, null_dist)
        self.assertLess(p_val, 0.5)

    def test_calculate_p_value_low_observed(self):
        """Test p-value when observed is low (within null distribution)."""
        observed = 0.15
        null_dist = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        
        # 0.2, 0.3, 0.4, 0.5 are >= 0.15 -> 4 values
        # p = (4 + 1) / (5 + 1) = 5/6
        p_val = calculate_p_value(observed, null_dist)
        expected = 5.0 / 6.0
        self.assertAlmostEqual(p_val, expected)

    def test_save_permutation_results(self):
        """Test saving results to CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_results.csv"
            
            observed = 0.5
            null_dist = np.array([0.1, 0.2, 0.3])
            p_val = 0.05
            time_taken = 10.0
            
            save_permutation_results(output_path, observed, null_dist, p_val, time_taken)
            
            self.assertTrue(output_path.exists())
            
            df = pd.read_csv(output_path)
            self.assertIn('metric', df.columns)
            self.assertIn('value', df.columns)
            
            # Check specific values
            metrics = df['metric'].tolist()
            values = df['value'].tolist()
            
            self.assertIn('observed_r2', metrics)
            self.assertIn('p_value', metrics)
            
            idx_obs = metrics.index('observed_r2')
            self.assertAlmostEqual(values[idx_obs], observed)


if __name__ == '__main__':
    unittest.main()