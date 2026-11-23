import os
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import numpy as np

# Import the function to test
from models.permutation_test import run_permutation_test

class TestPermutationTest(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures if needed."""
        pass

    @patch('models.permutation_test.load_loso_results')
    @patch('models.permutation_test.load_null_results')
    def test_permutation_significant_improvement(self, mock_null, mock_loso):
        """
        Test that the permutation test correctly identifies significant improvement
        when RF MAEs are consistently lower than Null MAEs.
        """
        # Mock data: RF consistently better (lower MAE)
        mock_loso.return_value = [
            {'fold_id': '1', 'mae': 10.0},
            {'fold_id': '2', 'mae': 12.0},
            {'fold_id': '3', 'mae': 8.0},
            {'fold_id': '4', 'mae': 15.0},
            {'fold_id': '5', 'mae': 11.0}
        ]
        mock_null.return_value = [
            {'fold_id': '1', 'mae': 20.0},
            {'fold_id': '2', 'mae': 22.0},
            {'fold_id': '3', 'mae': 18.0},
            {'fold_id': '4', 'mae': 25.0},
            {'fold_id': '5', 'mae': 21.0}
        ]

        # Run test with fewer permutations for speed in unit test
        # Seed 42 ensures reproducibility
        p_val = run_permutation_test(n_permutations=1000, seed=42)

        # Since RF is consistently better, p-value should be very low
        self.assertLess(p_val, 0.05, "P-value should be < 0.05 when RF is significantly better")
        self.assertGreaterEqual(p_val, 0.0, "P-value must be non-negative")
        self.assertLessEqual(p_val, 1.0, "P-value must be <= 1.0")

    @patch('models.permutation_test.load_loso_results')
    @patch('models.permutation_test.load_null_results')
    def test_permutation_no_improvement(self, mock_null, mock_loso):
        """
        Test that the permutation test returns high p-value when differences are random.
        """
        # Mock data: Random differences, some RF better, some Null better
        mock_loso.return_value = [
            {'fold_id': '1', 'mae': 15.0},
            {'fold_id': '2', 'mae': 12.0},
            {'fold_id': '3', 'mae': 18.0},
            {'fold_id': '4', 'mae': 10.0},
            {'fold_id': '5', 'mae': 14.0}
        ]
        mock_null.return_value = [
            {'fold_id': '1', 'mae': 14.0},
            {'fold_id': '2', 'mae': 13.0},
            {'fold_id': '3', 'mae': 17.0},
            {'fold_id': '4', 'mae': 11.0},
            {'fold_id': '5', 'mae': 15.0}
        ]

        p_val = run_permutation_test(n_permutations=1000, seed=123)
        
        # With random data, p-value should likely be > 0.05
        self.assertGreater(p_val, 0.05, "P-value should be > 0.05 when no significant difference exists")

    @patch('models.permutation_test.load_loso_results')
    @patch('models.permutation_test.load_null_results')
    def test_permutation_mismatched_folds(self, mock_null, mock_loso):
        """Test that mismatched fold counts raise an error."""
        mock_loso.return_value = [{'fold_id': '1', 'mae': 10.0}]
        mock_null.return_value = [
            {'fold_id': '1', 'mae': 20.0},
            {'fold_id': '2', 'mae': 20.0}
        ]

        with self.assertRaises(ValueError):
            run_permutation_test(n_permutations=100)

if __name__ == '__main__':
    unittest.main()