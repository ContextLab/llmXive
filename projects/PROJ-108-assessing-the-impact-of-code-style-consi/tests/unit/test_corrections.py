"""
Unit tests for multiple comparison corrections (Tukey HSD and Bonferroni).
Verifies logic for family-wise error rate control in statistical analysis.
"""

import unittest
import math
from typing import List, Tuple
from itertools import combinations

# Import the statistical utilities from the project's metrics module
# Note: We implement the correction logic here as it's a specific test utility
# or import from a hypothetical stats_utils if it existed in the API surface.
# Since the API surface only lists basic metrics, we implement the correction
# logic directly in the test to verify the mathematical correctness.

def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], List[bool]]:
    """
    Apply Bonferroni correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values.
        alpha: Significance level.
        
    Returns:
        Tuple of (adjusted_p_values, significant_flags)
    """
    n = len(p_values)
    if n == 0:
        return [], []
    
    adjusted = [min(p * n, 1.0) for p in p_values]
    significant = [p < alpha for p in adjusted]
    return adjusted, significant

def tukey_hsd_correction(group_means: List[float], group_sizes: List[int], 
                         mse: float, alpha: float = 0.05) -> List[Tuple[int, int, float, bool]]:
    """
    Perform Tukey HSD (Honestly Significant Difference) test logic.
    Calculates q-statistic for all pairs and compares against critical q.
    
    Note: This is a simplified implementation for testing the logic.
    In a full production environment, we would use `statsmodels` or `scipy`.
    Here we verify the calculation logic and the comparison mechanism.
    
    Args:
        group_means: Mean of each group.
        group_sizes: Number of observations in each group.
        mse: Mean Square Error from ANOVA.
        alpha: Significance level.
        
    Returns:
        List of tuples: (group_i, group_j, q_stat, is_significant)
    """
    k = len(group_means)
    if k < 2:
        return []
    
    # Approximate critical value for q (Studentized Range Statistic)
    # For testing purposes, we use a hardcoded lookup or approximation
    # df_error = sum(group_sizes) - k
    # In a real scenario, we'd look up q_table(df_error, k, alpha)
    # Here we assume a standard critical value for the test logic verification
    # e.g., q_crit for k=3, df=20, alpha=0.05 is approx 3.58
    # We will use a mock critical value to test the comparison logic
    q_crit = 3.58 
    
    results = []
    
    # Iterate over all unique pairs
    for i, j in combinations(range(k), 2):
        mean_diff = abs(group_means[i] - group_means[j])
        # Standard error of the difference
        # SE = sqrt(MSE * (1/n_i + 1/n_j) / 2) ? 
        # Actually Tukey SE = sqrt(MSE / 2 * (1/n_i + 1/n_j))
        # Or commonly: sqrt(MSE * (1/n_i + 1/n_j)) if using harmonic mean logic differently
        # Standard formula: q = (mean_i - mean_j) / sqrt(MSE * (1/n_i + 1/n_j) / 2)
        # Wait, standard Tukey HSD: q = (mean_i - mean_j) / sqrt(MSE * (1/n_i + 1/n_j) / 2)
        # Let's use the standard definition: q = diff / sqrt(MSE * (1/n_i + 1/n_j) / 2)
        
        se = math.sqrt(mse * (1.0/group_sizes[i] + 1.0/group_sizes[j]) / 2.0)
        if se == 0:
            q_stat = 0.0
        else:
            q_stat = mean_diff / se
        
        is_significant = q_stat > q_crit
        results.append((i, j, q_stat, is_significant))
        
    return results

class TestBonferroniCorrection(unittest.TestCase):
    
    def test_simple_correction(self):
        """Test basic Bonferroni multiplication."""
        p_vals = [0.01, 0.04, 0.06]
        adjusted, sig = bonferroni_correction(p_vals, alpha=0.05)
        
        # Expected: 0.01*3=0.03, 0.04*3=0.12, 0.06*3=0.18
        self.assertAlmostEqual(adjusted[0], 0.03, places=5)
        self.assertAlmostEqual(adjusted[1], 0.12, places=5)
        self.assertAlmostEqual(adjusted[2], 0.18, places=5)
        
        # Significance: 0.03 < 0.05 (True), 0.12 > 0.05 (False), 0.18 > 0.05 (False)
        self.assertTrue(sig[0])
        self.assertFalse(sig[1])
        self.assertFalse(sig[2])

    def test_cap_at_one(self):
        """Test that adjusted p-values are capped at 1.0."""
        p_vals = [0.5, 0.6, 0.7]
        adjusted, _ = bonferroni_correction(p_vals, alpha=0.05)
        
        self.assertEqual(adjusted[0], 1.0)
        self.assertEqual(adjusted[1], 1.0)
        self.assertEqual(adjusted[2], 1.0)

    def test_empty_list(self):
        """Test handling of empty input."""
        adjusted, sig = bonferroni_correction([], alpha=0.05)
        self.assertEqual(len(adjusted), 0)
        self.assertEqual(len(sig), 0)

class TestTukeyHSDCorrection(unittest.TestCase):
    
    def test_significant_difference(self):
        """Test Tukey HSD with clearly different groups."""
        # Group 0: mean=10, n=10
        # Group 1: mean=20, n=10
        # MSE = 5
        means = [10.0, 20.0]
        sizes = [10, 10]
        mse = 5.0
        
        # diff = 10
        # SE = sqrt(5 * (1/10 + 1/10) / 2) = sqrt(5 * 0.2 / 2) = sqrt(0.5) ≈ 0.707
        # q = 10 / 0.707 ≈ 14.14
        # q_crit (mock) = 3.58 -> Significant
        
        results = tukey_hsd_correction(means, sizes, mse)
        self.assertEqual(len(results), 1)
        
        i, j, q_stat, sig = results[0]
        self.assertEqual(i, 0)
        self.assertEqual(j, 1)
        self.assertTrue(sig)
        self.assertGreater(q_stat, 3.58)

    def test_no_significant_difference(self):
        """Test Tukey HSD with very similar groups."""
        means = [10.0, 10.1]
        sizes = [100, 100] # Large N reduces SE
        mse = 1.0 # Low variance
        
        # diff = 0.1
        # SE = sqrt(1 * (0.01 + 0.01) / 2) = sqrt(0.01) = 0.1
        # q = 0.1 / 0.1 = 1.0
        # 1.0 < 3.58 -> Not significant
        
        results = tukey_hsd_correction(means, sizes, mse)
        self.assertEqual(len(results), 1)
        _, _, q_stat, sig = results[0]
        self.assertFalse(sig)
        self.assertAlmostEqual(q_stat, 1.0, places=5)

    def test_multiple_groups(self):
        """Test with 3 groups to ensure all pairs are checked."""
        means = [10.0, 10.0, 20.0]
        sizes = [10, 10, 10]
        mse = 5.0
        
        results = tukey_hsd_correction(means, sizes, mse)
        self.assertEqual(len(results), 3) # (0,1), (0,2), (1,2)
        
        # (0,1) should be not significant (diff=0)
        # (0,2) should be significant
        # (1,2) should be significant
        
        sig_count = sum(1 for r in results if r[3])
        self.assertEqual(sig_count, 2)

if __name__ == '__main__':
    unittest.main()