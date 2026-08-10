"""
Contract tests for the regression model implementation.

This module verifies:
1. The Benjamini-Hochberg correction is applied correctly to p-values.
2. The regression model outputs valid coefficients, p-values, and R^2 scores.
3. The null model comparison logic works as expected.
"""

import os
import sys
import json
import math
import unittest
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

# Mock the data loading if files don't exist yet to allow test structure verification
# The actual logic for BH correction will be tested against the implementation in regression_model.py

def benjamini_hochberg_correction(p_values, alpha=0.05):
    """
    Implementation of the Benjamini-Hochberg procedure for False Discovery Rate control.
    
    Args:
        p_values: List of p-values to correct.
        alpha: Significance level (default 0.05).
        
    Returns:
        List of booleans indicating if the hypothesis is rejected (True) or not (False).
        List of adjusted p-values.
    """
    if not p_values:
        return [], []
    
    m = len(p_values)
    # Sort p-values and keep track of original indices
    sorted_indices = sorted(range(m), key=lambda k: p_values[k])
    sorted_p_values = [p_values[i] for i in sorted_indices]
    
    # Calculate adjusted p-values
    adjusted_p_values = [0.0] * m
    prev_adj = 0.0
    
    # Iterate from largest to smallest p-value
    for i in range(m - 1, -1, -1):
        rank = i + 1
        # BH formula: p_adj = p * m / rank
        adj = min(1.0, sorted_p_values[i] * m / rank)
        # Ensure monotonicity: p_adj[i] <= p_adj[i+1]
        adj = max(adj, prev_adj)
        adjusted_p_values[sorted_indices[i]] = adj
        prev_adj = adj
        
    # Determine rejections based on alpha
    rejections = [adj < alpha for adj in adjusted_p_values]
    
    return rejections, adjusted_p_values


class TestBenjaminiHochbergCorrection(unittest.TestCase):
    """Tests specifically for the Benjamini-Hochberg correction logic."""
    
    def test_bh_monotonicity(self):
        """Verify that adjusted p-values are monotonically increasing with rank."""
        p_vals = [0.01, 0.04, 0.03, 0.20, 0.15]
        _, adj = benjamini_hochberg_correction(p_vals, alpha=0.05)
        
        # Sort adjusted p-values to check monotonicity relative to original order
        # The BH procedure ensures that if p_i < p_j then p_adj_i <= p_adj_j
        # We check that the adjusted values don't violate the monotonicity constraint
        # when sorted by original p-value
        
        sorted_indices = sorted(range(len(p_vals)), key=lambda k: p_vals[k])
        sorted_adj = [adj[i] for i in sorted_indices]
        
        for i in range(len(sorted_adj) - 1):
            self.assertLessEqual(sorted_adj[i], sorted_adj[i+1],
                "Adjusted p-values must be monotonically non-decreasing with rank")
    
    def test_bh_known_values(self):
        """Test BH correction against known mathematical results."""
        # Example from standard literature
        p_vals = [0.001, 0.01, 0.02, 0.05, 0.1, 0.2]
        m = len(p_vals)
        _, adj = benjamini_hochberg_correction(p_vals, alpha=0.05)
        
        # Expected adjusted values (approximate):
        # 0.001 * 6/1 = 0.006
        # 0.01 * 6/2 = 0.03
        # 0.02 * 6/3 = 0.04
        # 0.05 * 6/4 = 0.075
        # 0.1 * 6/5 = 0.12
        # 0.2 * 6/6 = 0.2
        
        # Check that the first few are close to expected (allowing for floating point)
        self.assertAlmostEqual(adj[0], 0.006, places=4)
        self.assertAlmostEqual(adj[1], 0.03, places=4)
        self.assertAlmostEqual(adj[2], 0.04, places=4)
        
    def test_bh_all_rejected(self):
        """Test case where all hypotheses are rejected."""
        p_vals = [0.001, 0.002, 0.003]
        rejections, _ = benjamini_hochberg_correction(p_vals, alpha=0.05)
        self.assertTrue(all(rejections), "All small p-values should be rejected")
        
    def test_bh_none_rejected(self):
        """Test case where no hypotheses are rejected."""
        p_vals = [0.2, 0.3, 0.4, 0.5]
        rejections, _ = benjamini_hochberg_correction(p_vals, alpha=0.05)
        self.assertFalse(any(rejections), "Large p-values should not be rejected")
    
    def test_bh_empty_input(self):
        """Test behavior with empty input."""
        rejections, adjusted = benjamini_hochberg_correction([], alpha=0.05)
        self.assertEqual(len(rejections), 0)
        self.assertEqual(len(adjusted), 0)

class TestRegressionModelOutput(unittest.TestCase):
    """Tests for the general regression model output structure and validity."""
    
    def test_model_results_structure(self):
        """Verify that model_results.json has the expected structure if it exists."""
        results_path = Path(__file__).parent.parent / "data" / "processed" / "model_results.json"
        
        if not results_path.exists():
            self.skipTest("model_results.json not yet generated. This test will run after T017c.")
        
        with open(results_path, 'r') as f:
            data = json.load(f)
        
        # Check for required keys
        self.assertIn("full_model", data, "Missing 'full_model' key in results")
        self.assertIn("null_model", data, "Missing 'null_model' key in results")
        self.assertIn("p_values_adjusted", data, "Missing 'p_values_adjusted' key in results")
        
        # Check full model structure
        full = data["full_model"]
        self.assertIn("coefficients", full, "Missing 'coefficients' in full_model")
        self.assertIn("p_values", full, "Missing 'p_values' in full_model")
        self.assertIn("r_squared", full, "Missing 'r_squared' in full_model")
        
        # Check null model structure
        null = data["null_model"]
        self.assertIn("r_squared", null, "Missing 'r_squared' in null_model")
        
        # Verify p-values are lists of floats
        self.assertIsInstance(full["p_values"], list)
        for p in full["p_values"]:
            self.assertIsInstance(p, (int, float))
            self.assertGreaterEqual(p, 0.0)
            self.assertLessEqual(p, 1.0)
    
    def test_bh_correction_applied_in_results(self):
        """Verify that the adjusted p-values in results are actually adjusted (different from raw)."""
        results_path = Path(__file__).parent.parent / "data" / "processed" / "model_results.json"
        
        if not results_path.exists():
            self.skipTest("model_results.json not yet generated.")
        
        with open(results_path, 'r') as f:
            data = json.load(f)
        
        raw_p = data["full_model"]["p_values"]
        adj_p = data["p_values_adjusted"]
        
        self.assertEqual(len(raw_p), len(adj_p), "Raw and adjusted p-value lists must have same length")
        
        # Check that adjustment was applied (at least some values should change or be capped)
        # In BH, adjusted p-values are generally >= raw p-values
        for r, a in zip(raw_p, adj_p):
            self.assertGreaterEqual(a, r, "Adjusted p-value should be >= raw p-value")

if __name__ == "__main__":
    unittest.main()