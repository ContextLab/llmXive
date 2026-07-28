"""
Unit tests for Holm-Bonferroni correction logic in modeling.py.

This module tests the statistical correction logic required for User Story 3.
It verifies that p-values are correctly adjusted and that the ordering
and thresholding logic matches the Holm-Bonferroni method.
"""
import unittest
import math
from typing import List, Dict, Any
import sys
import os

# Add project root to path for imports if running directly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.modeling import apply_holm_bonferroni

class TestHolmBonferroniCorrection(unittest.TestCase):
    """Tests for the Holm-Bonferroni correction implementation."""

    def test_basic_correction_ordering(self):
        """Test that p-values are sorted correctly before adjustment."""
        # Unsorted p-values
        p_values = [0.05, 0.01, 0.10, 0.02]
        features = ['feat_a', 'feat_b', 'feat_c', 'feat_d']
        
        result = apply_holm_bonferroni(p_values, features)
        
        # The result should be sorted by original p-value ascending
        # Expected sorted order: 0.01 (b), 0.02 (d), 0.05 (a), 0.10 (c)
        # Adjusted p-values:
        # 1. 0.01 * 4 = 0.04
        # 2. 0.02 * 3 = 0.06
        # 3. 0.05 * 2 = 0.10
        # 4. 0.10 * 1 = 0.10
        
        self.assertEqual(len(result), 4)
        self.assertAlmostEqual(result[0]['adjusted_p'], 0.04, places=5)
        self.assertEqual(result[0]['feature'], 'feat_b')
        
        self.assertAlmostEqual(result[1]['adjusted_p'], 0.06, places=5)
        self.assertEqual(result[1]['feature'], 'feat_d')

    def test_cumulative_monotonicity(self):
        """Test that adjusted p-values are monotonically non-decreasing."""
        # Create a scenario where simple multiplication would decrease
        # but Holm-Bonferroni enforces monotonicity
        p_values = [0.01, 0.02, 0.03]
        features = ['f1', 'f2', 'f3']
        
        result = apply_holm_bonferroni(p_values, features)
        
        adjusted = [r['adjusted_p'] for r in result]
        
        # Check monotonicity: adjusted[i] <= adjusted[i+1]
        for i in range(len(adjusted) - 1):
            self.assertLessEqual(adjusted[i], adjusted[i+1],
                                 f"Monotonicity violation at index {i}: {adjusted[i]} > {adjusted[i+1]}")

    def test_edge_case_single_pvalue(self):
        """Test correction with a single p-value."""
        p_values = [0.05]
        features = ['single_feature']
        
        result = apply_holm_bonferroni(p_values, features)
        
        # For n=1, adjusted = p * 1
        self.assertAlmostEqual(result[0]['adjusted_p'], 0.05, places=5)
        self.assertTrue(result[0]['significant'])

    def test_edge_case_all_significant(self):
        """Test case where all p-values remain significant after correction."""
        p_values = [0.001, 0.002, 0.003]
        features = ['f1', 'f2', 'f3']
        
        result = apply_holm_bonferroni(p_values, features)
        
        # 0.001 * 3 = 0.003 (sig)
        # 0.002 * 2 = 0.004 (sig)
        # 0.003 * 1 = 0.003 (sig)
        for r in result:
            self.assertTrue(r['significant'])

    def test_edge_case_none_significant(self):
        """Test case where no p-values remain significant."""
        p_values = [0.1, 0.2, 0.3]
        features = ['f1', 'f2', 'f3']
        
        result = apply_holm_bonferroni(p_values, features)
        
        # 0.1 * 3 = 0.3 (not sig)
        # 0.2 * 2 = 0.4 (not sig)
        # 0.3 * 1 = 0.3 (not sig)
        for r in result:
            self.assertFalse(r['significant'])

    def test_significance_threshold(self):
        """Test that the significance threshold (alpha=0.05) is applied correctly."""
        # Construct a case where the boundary is critical
        # n=2. p1=0.02, p2=0.04
        # 0.02 * 2 = 0.04 (sig)
        # 0.04 * 1 = 0.04 (sig)
        p_values = [0.02, 0.04]
        features = ['f1', 'f2']
        
        result = apply_holm_bonferroni(p_values, features)
        
        # Both should be significant
        self.assertTrue(result[0]['significant'])
        self.assertTrue(result[1]['significant'])

    def test_input_validation_empty(self):
        """Test handling of empty input lists."""
        with self.assertRaises(ValueError):
            apply_holm_bonferroni([], [])

    def test_input_validation_mismatched_lengths(self):
        """Test handling of mismatched p-values and features lengths."""
        with self.assertRaises(ValueError):
            apply_holm_bonferroni([0.05, 0.01], ['f1'])

    def test_realistic_medical_scenario(self):
        """Test with a realistic set of p-values from a medical study."""
        # Simulating p-values from a logistic regression on medical features
        p_values = [0.001, 0.045, 0.08, 0.20, 0.50]
        features = ['age', 'blood_pressure', 'cholesterol', 'smoking', 'diet']
        
        result = apply_holm_bonferroni(p_values, features)
        
        # Expected calculations:
        # Sorted: 0.001, 0.045, 0.08, 0.20, 0.50
        # 1: 0.001 * 5 = 0.005 (sig)
        # 2: 0.045 * 4 = 0.180 (not sig)
        # 3: 0.08 * 3 = 0.24 (not sig) -> capped at 1.0? No, just compared to alpha
        # ...
        
        # Check that the first one is significant
        self.assertTrue(result[0]['significant'])
        
        # Check that the second one (0.045 * 4 = 0.18) is NOT significant
        self.assertFalse(result[1]['significant'])
        
        # Verify monotonicity
        adjusted = [r['adjusted_p'] for r in result]
        for i in range(len(adjusted) - 1):
            self.assertLessEqual(adjusted[i], adjusted[i+1])

if __name__ == '__main__':
    unittest.main()