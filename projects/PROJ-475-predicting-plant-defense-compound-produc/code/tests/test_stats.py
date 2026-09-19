import unittest
import sys
import os
import tempfile
import shutil
from pathlib import Path
import numpy as np
import pandas as pd

# Import the functions we are testing from the stats module
from utils.stats import benjamini_hochberg_correction, calculate_jaccard_index, calculate_jaccard_index_from_lists

class TestBenjaminiHochbergCorrection(unittest.TestCase):
    """
    Unit tests for the Benjamini-Hochberg (BH) correction implementation (T032).
    Tests verify:
    1. Correct calculation of adjusted p-values.
    2. Handling of edge cases (all 0, all 1).
    3. Monotonicity of adjusted p-values.
    """

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_bh_correction_basic(self):
        """Test BH correction on a known set of p-values."""
        # Example p-values
        p_values = np.array([0.01, 0.04, 0.03, 0.005, 0.02, 0.05])
        m = len(p_values)
        
        # Expected logic:
        # Sort p-values: [0.005, 0.01, 0.02, 0.03, 0.04, 0.05]
        # Ranks (1-indexed): [1, 2, 3, 4, 5, 6]
        # Thresholds (i/m * alpha): [0.0083, 0.0166, 0.0333, 0.05, 0.0666, 0.0833] (alpha=0.05)
        # Adjusted p-values (naive): p * m / i
        # Corrected (monotonicity enforced):
        
        # We test the function's ability to run and return an array of the same shape
        result = benjamini_hochberg_correction(p_values, alpha=0.05)
        
        self.assertIsInstance(result, np.ndarray)
        self.assertEqual(result.shape, p_values.shape)
        # Adjusted p-values should be between 0 and 1
        self.assertTrue(np.all(result >= 0.0))
        self.assertTrue(np.all(result <= 1.0))
        
        # Check monotonicity of the result (adjusted p-values should be non-decreasing with rank)
        # Note: The function returns values in the original order, so we must sort them by original rank to check monotonicity
        # But a simpler check is that if we sort the result by the original p-values, the adjusted values should be non-decreasing
        sorted_indices = np.argsort(p_values)
        sorted_result = result[sorted_indices]
        self.assertTrue(np.all(np.diff(sorted_result) >= -1e-9)) # Allow small float tolerance

    def test_bh_correction_all_zeros(self):
        """Test BH correction when all p-values are 0."""
        p_values = np.array([0.0, 0.0, 0.0])
        result = benjamini_hochberg_correction(p_values, alpha=0.05)
        self.assertTrue(np.all(result == 0.0))

    def test_bh_correction_all_ones(self):
        """Test BH correction when all p-values are 1."""
        p_values = np.array([1.0, 1.0, 1.0])
        result = benjamini_hochberg_correction(p_values, alpha=0.05)
        # Adjusted p-values for 1.0 should be 1.0 (capped)
        self.assertTrue(np.all(result == 1.0))

    def test_bh_correction_monotonicity_enforcement(self):
        """Test that the BH correction enforces monotonicity (step-up procedure)."""
        # Construct a case where naive calculation would violate monotonicity
        # p-values: [0.01, 0.10] -> sorted: [0.01, 0.10]
        # m=2, alpha=0.05
        # i=1: 0.01 * 2 / 1 = 0.02
        # i=2: 0.10 * 2 / 2 = 0.10
        # This is already monotonic.
        # Let's try: [0.04, 0.05] -> sorted: [0.04, 0.05]
        # i=1: 0.04 * 2 / 1 = 0.08
        # i=2: 0.05 * 2 / 2 = 0.05
        # Naive: [0.08, 0.05] -> Violation. Corrected: [0.08, 0.08] (since 0.08 > 0.05, we take min(0.08, 0.08) from right to left? No, step-up ensures p_adj[i] <= p_adj[i+1])
        # Actually, the standard algorithm ensures p_adj[i] <= p_adj[i+1] by taking min(p_adj[i], p_adj[i+1]) from right to left.
        # So if p_adj[1] = 0.08 and p_adj[2] = 0.05, we set p_adj[1] = min(0.08, 0.05) = 0.05? No, that would be wrong.
        # The algorithm is:
        # 1. Sort p-values: p(1) <= p(2) <= ... <= p(m)
        # 2. Calculate q(i) = p(i) * m / i
        # 3. Enforce monotonicity: q'(i) = min(q(i), q'(i+1)) for i = m-1 down to 1.
        # So if q(1)=0.08, q(2)=0.05, then q'(2)=0.05, q'(1)=min(0.08, 0.05)=0.05.
        # Wait, that means the smaller p-value gets the same adjusted p-value as the larger one?
        # Yes, because if the larger one is not significant, the smaller one might be, but the monotonicity constraint forces them to be consistent.
        # Actually, the standard definition is:
        # p_adj(i) = min_{k >= i} ( p(k) * m / k )
        # So for i=1: min(0.08, 0.05) = 0.05.
        # So the result for [0.04, 0.05] should be [0.05, 0.05] (after sorting back).
        
        p_values = np.array([0.04, 0.05])
        result = benjamini_hochberg_correction(p_values, alpha=0.05)
        
        # The adjusted p-values should be monotonic with respect to the original p-values
        # Since 0.04 < 0.05, we expect result[0] <= result[1]
        self.assertTrue(result[0] <= result[1])
        
        # Specifically, for this case, both should be 0.05 (or close to it due to float precision)
        # 0.04 * 2 / 1 = 0.08
        # 0.05 * 2 / 2 = 0.05
        # Corrected: min(0.08, 0.05) = 0.05 for the first one, 0.05 for the second.
        # So result should be approximately [0.05, 0.05]
        self.assertAlmostEqual(result[0], 0.05, places=5)
        self.assertAlmostEqual(result[1], 0.05, places=5)

class TestJaccardIndex(unittest.TestCase):
    """
    Unit tests for Jaccard index calculations (T031).
    Tests verify:
    1. Correct calculation for sets.
    2. Correct calculation for lists (with duplicates handling).
    3. Edge cases (empty sets, identical sets).
    """

    def test_jaccard_index_identical_sets(self):
        """Test Jaccard index for identical sets."""
        set_a = {1, 2, 3}
        set_b = {1, 2, 3}
        index = calculate_jaccard_index(set_a, set_b)
        self.assertEqual(index, 1.0)

    def test_jaccard_index_disjoint_sets(self):
        """Test Jaccard index for disjoint sets."""
        set_a = {1, 2, 3}
        set_b = {4, 5, 6}
        index = calculate_jaccard_index(set_a, set_b)
        self.assertEqual(index, 0.0)

    def test_jaccard_index_partial_overlap(self):
        """Test Jaccard index for partially overlapping sets."""
        set_a = {1, 2, 3, 4}
        set_b = {3, 4, 5, 6}
        # Intersection: {3, 4} -> size 2
        # Union: {1, 2, 3, 4, 5, 6} -> size 6
        # Jaccard: 2/6 = 0.333...
        index = calculate_jaccard_index(set_a, set_b)
        self.assertAlmostEqual(index, 1/3, places=5)

    def test_jaccard_index_empty_sets(self):
        """Test Jaccard index for empty sets."""
        set_a = set()
        set_b = set()
        # By convention, Jaccard of two empty sets is 1.0 (or 0.0 depending on definition, but usually 1)
        # Our implementation should handle this.
        index = calculate_jaccard_index(set_a, set_b)
        self.assertEqual(index, 1.0)

    def test_jaccard_index_one_empty_set(self):
        """Test Jaccard index when one set is empty."""
        set_a = {1, 2, 3}
        set_b = set()
        index = calculate_jaccard_index(set_a, set_b)
        self.assertEqual(index, 0.0)

    def test_jaccard_index_from_lists_identical(self):
        """Test Jaccard index from lists for identical lists."""
        list_a = [1, 2, 3, 2]
        list_b = [2, 3, 1, 3]
        # As sets: {1, 2, 3} and {1, 2, 3} -> Jaccard 1.0
        index = calculate_jaccard_index_from_lists(list_a, list_b)
        self.assertEqual(index, 1.0)

    def test_jaccard_index_from_lists_partial_overlap(self):
        """Test Jaccard index from lists for partially overlapping lists."""
        list_a = [1, 2, 3, 4]
        list_b = [3, 4, 5, 6]
        # As sets: {1, 2, 3, 4} and {3, 4, 5, 6} -> Intersection {3,4}, Union {1,2,3,4,5,6}
        index = calculate_jaccard_index_from_lists(list_a, list_b)
        self.assertAlmostEqual(index, 1/3, places=5)

    def test_jaccard_index_from_lists_empty(self):
        """Test Jaccard index from lists for empty lists."""
        list_a = []
        list_b = []
        index = calculate_jaccard_index_from_lists(list_a, list_b)
        self.assertEqual(index, 1.0)

    def test_jaccard_index_from_lists_one_empty(self):
        """Test Jaccard index from lists when one list is empty."""
        list_a = [1, 2, 3]
        list_b = []
        index = calculate_jaccard_index_from_lists(list_a, list_b)
        self.assertEqual(index, 0.0)

if __name__ == '__main__':
    unittest.main()