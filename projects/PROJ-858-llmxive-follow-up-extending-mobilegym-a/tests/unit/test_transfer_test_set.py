"""
Unit tests for T029: Transfer Test Set Generation.

These tests verify the logic of identifying held-out variables
without requiring the full pipeline to run, by mocking the inputs.
"""
import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from analysis.transfer_test_set import get_observed_variables, generate_held_out_test_set

class TestTransferTestSetGeneration(unittest.TestCase):

    def test_get_observed_variables_dict_format(self):
        """Test extraction of observed variables from dict-based vectors."""
        vectors = [
            {"dark_mode": 1, "unread_count": 0, "location": 0},
            {"dark_mode": 2, "unread_count": 5, "location": 0},
            {"dark_mode": 0, "unread_count": 0, "location": 1}
        ]
        observed = get_observed_variables(vectors)
        self.assertIn("dark_mode", observed)
        self.assertIn("unread_count", observed)
        self.assertIn("location", observed)
        self.assertEqual(len(observed), 3)

    def test_get_observed_variables_nested_format(self):
        """Test extraction from nested count format."""
        vectors = [
            {"dark_mode": {"count": 1}, "unread_count": {"count": 0}},
            {"dark_mode": {"count": 0}, "unread_count": {"count": 3}}
        ]
        observed = get_observed_variables(vectors)
        self.assertIn("dark_mode", observed)
        self.assertIn("unread_count", observed)
        self.assertEqual(len(observed), 2)

    @patch('analysis.transfer_test_set.get_semantic_proxies')
    @patch('analysis.transfer_test_set.load_aggregated_vectors')
    def test_held_out_calculation_logic(self, mock_load_vectors, mock_get_proxies):
        """Test that held-out variables are correctly calculated as (All - Observed)."""
        # Mock schema: A, B, C
        mock_get_proxies.return_value = ["var_A", "var_B", "var_C"]
        
        # Mock training data: Only observed var_A and var_B
        mock_load_vectors.return_value = [
            {"var_A": 1, "var_B": 1, "var_C": 0}
        ]
        
        result = generate_held_out_test_set()
        
        self.assertEqual(result['total_schema_variables'], 3)
        self.assertEqual(result['observed_in_training'], 2)
        self.assertEqual(result['held_out_count'], 1)
        self.assertIn("var_C", result['held_out_variables'])
        self.assertNotIn("var_A", result['held_out_variables'])
        self.assertNotIn("var_B", result['held_out_variables'])

    @patch('analysis.transfer_test_set.get_semantic_proxies')
    @patch('analysis.transfer_test_set.load_aggregated_vectors')
    def test_all_observed_no_held_out(self, mock_load_vectors, mock_get_proxies):
        """Test case where all variables are observed (held-out is empty)."""
        mock_get_proxies.return_value = ["var_A", "var_B"]
        mock_load_vectors.return_value = [
            {"var_A": 1, "var_B": 1}
        ]
        
        result = generate_held_out_test_set()
        
        self.assertEqual(result['held_out_count'], 0)
        self.assertEqual(result['held_out_variables'], [])

    @patch('analysis.transfer_test_set.get_semantic_proxies')
    @patch('analysis.transfer_test_set.load_aggregated_vectors')
    def test_none_observed_all_held_out(self, mock_load_vectors, mock_get_proxies):
        """Test case where no variables are observed (all are held-out)."""
        mock_get_proxies.return_value = ["var_A", "var_B"]
        mock_load_vectors.return_value = [
            {"var_A": 0, "var_B": 0}
        ]
        
        result = generate_held_out_test_set()
        
        self.assertEqual(result['held_out_count'], 2)
        self.assertIn("var_A", result['held_out_variables'])
        self.assertIn("var_B", result['held_out_variables'])

if __name__ == '__main__':
    unittest.main()
