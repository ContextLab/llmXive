import unittest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

# Add code to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from model_training import calculate_permutation_importance, get_memory_usage_mb

class TestPermutationImportance(unittest.TestCase):
    
    def setUp(self):
        # Create a simple mock dataset
        np.random.seed(42)
        n_samples = 100
        n_features = 5
        
        self.X = pd.DataFrame(
            np.random.rand(n_samples, n_features),
            columns=[f"feature_{i}" for i in range(n_features)]
        )
        self.y = pd.Series(np.random.randint(0, 2, n_samples))
        
        # Create a dummy model (we won't actually train a real RF for this unit test
        # to avoid heavy dependencies, but we mock the prediction behavior)
        self.mock_model = MagicMock()
        self.mock_model.score = MagicMock(return_value=0.8)
        
    def test_calculate_permutation_importance_structure(self):
        """
        Verify that the returned DataFrame has the correct columns and shape.
        """
        # Mock the internal permutation_importance function to return deterministic data
        with patch('model_training.permutation_importance') as mock_perm:
            mock_perm.return_value.importances_mean = np.array([0.5, 0.2, 0.1, 0.05, 0.01])
            mock_perm.return_value.importances_std = np.array([0.1, 0.05, 0.02, 0.01, 0.005])
            
            df = calculate_permutation_importance(self.mock_model, self.X, self.y)
            
            self.assertIn('feature', df.columns)
            self.assertIn('importance_mean', df.columns)
            self.assertIn('importance_std', df.columns)
            self.assertIn('rank', df.columns)
            self.assertEqual(len(df), 5)
            
            # Verify sorting (descending by mean)
            self.assertTrue(df['importance_mean'].is_monotonic_decreasing)
            
    def test_rank_assignment(self):
        """
        Verify that ranks are assigned correctly 1 to N.
        """
        with patch('model_training.permutation_importance') as mock_perm:
            mock_perm.return_value.importances_mean = np.array([0.1, 0.3, 0.2, 0.05, 0.01])
            mock_perm.return_value.importances_std = np.zeros(5)
            
            df = calculate_permutation_importance(self.mock_model, self.X, self.y)
            
            # Expected order after sorting: 0.3, 0.2, 0.1, 0.05, 0.01
            # Ranks should be 1, 2, 3, 4, 5
            self.assertEqual(df.iloc[0]['rank'], 1)
            self.assertEqual(df.iloc[1]['rank'], 2)
            self.assertEqual(df.iloc[4]['rank'], 5)

class TestMemoryUtils(unittest.TestCase):
    def test_get_memory_usage_mb_returns_float(self):
        """Verify memory usage function returns a float."""
        mem = get_memory_usage_mb()
        self.assertIsInstance(mem, float)

if __name__ == '__main__':
    unittest.main()