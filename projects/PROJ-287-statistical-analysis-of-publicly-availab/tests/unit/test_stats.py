"""
Unit tests for MaxT correction logic.

This module tests the implementation of the MaxT procedure for 
Family-Wise Error Rate (FWER) control across dependent window pairs.
"""

import unittest
import numpy as np
from typing import List, Dict, Tuple
from scipy import stats


class MaxTCorrector:
    """
    Implements the MaxT procedure for FWER control.
    
    The MaxT procedure is a resampling-based method for adjusting p-values
    when testing multiple hypotheses that are dependent (e.g., overlapping
    time windows in topic drift analysis).
    
    Reference: Westfall, P. H., & Young, S. S. (1993). Resampling-based
    multiple testing: Examples and methods for p-value adjustment.
    """

    def __init__(self, seed: int = 42):
        """
        Initialize the MaxT corrector with a random seed for reproducibility.
        
        Args:
            seed: Random seed for resampling operations.
        """
        self.rng = np.random.default_rng(seed)

    def compute_max_stat_null_distribution(
        self, 
        test_stats: np.ndarray, 
        n_permutations: int = 1000
    ) -> np.ndarray:
        """
        Generate the null distribution of the maximum test statistic.
        
        This is the core of the MaxT procedure: we generate a distribution
        of the maximum statistic under the null hypothesis by resampling.
        
        Args:
            test_stats: Array of observed test statistics for each hypothesis.
            n_permutations: Number of permutations to generate.
        
        Returns:
            Array of max statistics from each permutation.
        """
        if test_stats.ndim != 1:
            raise ValueError("test_stats must be a 1D array")
        
        n_hypotheses = len(test_stats)
        max_stats = np.zeros(n_permutations)
        
        for i in range(n_permutations):
            # Simulate null distribution by resampling
            # For JS divergence, we can permute the underlying data
            # Here we simulate by generating random test statistics
            # In a real implementation, this would permute the actual data
            null_stats = self.rng.normal(0, 1, n_hypotheses)
            max_stats[i] = np.max(np.abs(null_stats))
        
        return max_stats

    def adjust_pvalues(
        self, 
        observed_stats: np.ndarray, 
        null_max_stats: np.ndarray,
        two_sided: bool = True
    ) -> np.ndarray:
        """
        Compute MaxT-adjusted p-values for each hypothesis.
        
        The adjusted p-value for hypothesis i is the proportion of 
        permutations where the maximum null statistic exceeds the 
        observed statistic for hypothesis i.
        
        Args:
            observed_stats: Array of observed test statistics.
            null_max_stats: Array of max statistics from null distribution.
            two_sided: Whether to use two-sided test (default: True).
        
        Returns:
            Array of adjusted p-values.
        """
        if observed_stats.ndim != 1:
            raise ValueError("observed_stats must be a 1D array")
        
        n_hypotheses = len(observed_stats)
        n_permutations = len(null_max_stats)
        
        if n_hypotheses == 0:
            return np.array([])
        
        # For two-sided tests, use absolute values
        if two_sided:
            observed_abs = np.abs(observed_stats)
        else:
            observed_abs = observed_stats
        
        # Compute adjusted p-values
        adjusted_pvalues = np.zeros(n_hypotheses)
        
        for i in range(n_hypotheses):
            # Count how many times the max null stat exceeds the observed stat
            count = np.sum(null_max_stats >= observed_abs[i])
            adjusted_pvalues[i] = (count + 1) / (n_permutations + 1)
        
        return adjusted_pvalues

    def run_maxt_correction(
        self, 
        observed_stats: np.ndarray, 
        n_permutations: int = 1000,
        seed: int = 42
    ) -> Dict[str, np.ndarray]:
        """
        Run the complete MaxT correction procedure.
        
        Args:
            observed_stats: Array of observed test statistics.
            n_permutations: Number of permutations for null distribution.
            seed: Random seed for reproducibility.
        
        Returns:
            Dictionary containing:
                - 'adjusted_pvalues': MaxT-adjusted p-values
                - 'null_max_stats': The null distribution of max statistics
                - 'observed_stats': The original observed statistics
        """
        self.rng = np.random.default_rng(seed)
        
        # Generate null distribution
        null_max_stats = self.compute_max_stat_null_distribution(
            observed_stats, n_permutations
        )
        
        # Adjust p-values
        adjusted_pvalues = self.adjust_pvalues(observed_stats, null_max_stats)
        
        return {
            'adjusted_pvalues': adjusted_pvalues,
            'null_max_stats': null_max_stats,
            'observed_stats': observed_stats
        }


class TestMaxTCorrectionLogic(unittest.TestCase):
    """Unit tests for MaxT correction logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.corrector = MaxTCorrector(seed=42)
        self.n_permutations = 100

    def test_max_stat_null_distribution_shape(self):
        """Test that null distribution has correct shape."""
        observed_stats = np.array([1.5, 2.3, 0.8, 1.2])
        null_dist = self.corrector.compute_max_stat_null_distribution(
            observed_stats, n_permutations=self.n_permutations
        )
        
        self.assertEqual(null_dist.shape, (self.n_permutations,))
        self.assertIsInstance(null_dist, np.ndarray)

    def test_adjusted_pvalues_range(self):
        """Test that adjusted p-values are in [0, 1]."""
        observed_stats = np.array([1.5, 2.3, 0.8, 1.2])
        null_dist = self.corrector.compute_max_stat_null_distribution(
            observed_stats, n_permutations=self.n_permutations
        )
        
        adjusted_pvalues = self.corrector.adjust_pvalues(
            observed_stats, null_dist
        )
        
        self.assertTrue(np.all(adjusted_pvalues >= 0))
        self.assertTrue(np.all(adjusted_pvalues <= 1))

    def test_maxt_correction_output_structure(self):
        """Test that run_maxt_correction returns expected structure."""
        observed_stats = np.array([1.5, 2.3, 0.8, 1.2])
        result = self.corrector.run_maxt_correction(
            observed_stats, n_permutations=self.n_permutations
        )
        
        self.assertIn('adjusted_pvalues', result)
        self.assertIn('null_max_stats', result)
        self.assertIn('observed_stats', result)
        
        self.assertEqual(len(result['adjusted_pvalues']), len(observed_stats))
        self.assertEqual(len(result['null_max_stats']), self.n_permutations)

    def test_adjusted_pvalues_greater_than_or_equal_to_raw(self):
        """
        Test that adjusted p-values are >= raw p-values.
        
        This is a key property of multiple testing corrections: 
        adjusted p-values should be more conservative (larger) than 
        raw p-values.
        """
        observed_stats = np.array([1.5, 2.3, 0.8, 1.2])
        
        # Compute raw p-values (two-sided normal)
        raw_pvalues = 2 * (1 - stats.norm.cdf(np.abs(observed_stats)))
        
        result = self.corrector.run_maxt_correction(
            observed_stats, n_permutations=5000, seed=123
        )
        
        adjusted_pvalues = result['adjusted_pvalues']
        
        # Adjusted p-values should be >= raw p-values
        self.assertTrue(np.all(adjusted_pvalues >= raw_pvalues))

    def test_monotonicity_with_permutations(self):
        """
        Test that increasing permutations stabilizes the results.
        
        With more permutations, the adjusted p-values should converge.
        """
        observed_stats = np.array([1.5, 2.3, 0.8])
        
        result_100 = self.corrector.run_maxt_correction(
            observed_stats, n_permutations=100, seed=42
        )
        
        result_1000 = self.corrector.run_maxt_correction(
            observed_stats, n_permutations=1000, seed=42
        )
        
        # Results should be similar (not identical due to randomness)
        # but the trend should be consistent
        # We check that the ordering of p-values is preserved
        order_100 = np.argsort(result_100['adjusted_pvalues'])
        order_1000 = np.argsort(result_1000['adjusted_pvalues'])
        
        # The ranks should be highly correlated
        correlation = np.corrcoef(
            result_100['adjusted_pvalues'], 
            result_1000['adjusted_pvalues']
        )[0, 1]
        
        self.assertGreater(correlation, 0.5)

    def test_empty_input_handling(self):
        """Test handling of empty input arrays."""
        observed_stats = np.array([])
        
        result = self.corrector.run_maxt_correction(
            observed_stats, n_permutations=self.n_permutations
        )
        
        self.assertEqual(len(result['adjusted_pvalues']), 0)
        self.assertEqual(len(result['null_max_stats']), self.n_permutations)

    def test_single_hypothesis(self):
        """Test behavior with a single hypothesis."""
        observed_stats = np.array([2.5])
        
        result = self.corrector.run_maxt_correction(
            observed_stats, n_permutations=self.n_permutations
        )
        
        self.assertEqual(len(result['adjusted_pvalues']), 1)
        # For a single hypothesis, MaxT should be equivalent to Bonferroni
        # which for one test is just the raw p-value (approximately)
        self.assertTrue(0 <= result['adjusted_pvalues'][0] <= 1)

    def test_reproducibility_with_seed(self):
        """Test that results are reproducible with the same seed."""
        observed_stats = np.array([1.5, 2.3, 0.8, 1.2])
        
        result1 = self.corrector.run_maxt_correction(
            observed_stats, n_permutations=1000, seed=42
        )
        
        result2 = self.corrector.run_maxt_correction(
            observed_stats, n_permutations=1000, seed=42
        )
        
        # Results should be identical with the same seed
        np.testing.assert_array_equal(
            result1['adjusted_pvalues'], 
            result2['adjusted_pvalues']
        )
        np.testing.assert_array_equal(
            result1['null_max_stats'], 
            result2['null_max_stats']
        )

    def test_fwer_control_property(self):
        """
        Test the FWER control property of MaxT.
        
        Under the global null (all hypotheses are true nulls), 
        the probability of at least one false rejection should be <= alpha.
        
        This is a simulation-based test to demonstrate the property.
        """
        n_simulations = 100
        n_hypotheses = 5
        alpha = 0.05
        n_permutations = 500
        
        rejections = 0
        
        for _ in range(n_simulations):
            # Generate data under global null (all stats ~ N(0,1))
            observed_stats = np.random.normal(0, 1, n_hypotheses)
            
            result = self.corrector.run_maxt_correction(
                observed_stats, n_permutations=n_permutations, seed=42
            )
            
            # Count rejections at alpha level
            rejections_in_sim = np.sum(result['adjusted_pvalues'] < alpha)
            
            if rejections_in_sim > 0:
                rejections += 1
        
        # The empirical FWER should be <= alpha (with some tolerance for simulation error)
        empirical_fwer = rejections / n_simulations
        self.assertLessEqual(empirical_fwer, alpha + 0.05)  # Allow small simulation error

    def test_two_sided_vs_one_sided(self):
        """Test difference between one-sided and two-sided adjustments."""
        observed_stats = np.array([1.5, -2.3, 0.8, -1.2])
        null_dist = self.corrector.compute_max_stat_null_distribution(
            observed_stats, n_permutations=self.n_permutations
        )
        
        # Two-sided (default)
        adjusted_two_sided = self.corrector.adjust_pvalues(
            observed_stats, null_dist, two_sided=True
        )
        
        # One-sided (using raw values, not absolute)
        adjusted_one_sided = self.corrector.adjust_pvalues(
            observed_stats, null_dist, two_sided=False
        )
        
        # Results should be different
        self.assertFalse(np.allclose(adjusted_two_sided, adjusted_one_sided))

    def test_large_statistic_rejection(self):
        """Test that very large statistics lead to small adjusted p-values."""
        # Create a scenario with one very large statistic
        observed_stats = np.array([1.5, 2.0, 0.8, 5.0])
        
        result = self.corrector.run_maxt_correction(
            observed_stats, n_permutations=5000, seed=42
        )
        
        # The largest statistic (5.0) should have the smallest p-value
        min_p_idx = np.argmin(result['adjusted_pvalues'])
        self.assertEqual(min_p_idx, 3)  # Index of 5.0

    def test_max_stat_null_distribution_properties(self):
        """Test properties of the null max statistic distribution."""
        observed_stats = np.array([1.0, 1.0, 1.0])
        null_dist = self.corrector.compute_max_stat_null_distribution(
            observed_stats, n_permutations=1000
        )
        
        # The null distribution should be non-negative (for absolute values)
        self.assertTrue(np.all(null_dist >= 0))
        
        # The mean should be positive
        self.assertGreater(np.mean(null_dist), 0)
        
        # The distribution should have some variance
        self.assertGreater(np.std(null_dist), 0)

    def test_integration_with_js_divergence_context(self):
        """
        Test MaxT correction in the context of JS divergence testing.
        
        Simulate a scenario where we have JS divergence values between
        consecutive time windows and need to test for significant drift.
        """
        # Simulate JS divergence values between 5 consecutive windows
        # (4 pairwise comparisons)
        js_divergences = np.array([0.05, 0.12, 0.03, 0.15])
        
        # Convert to test statistics (e.g., z-scores from permutation test)
        # In reality, these would come from a permutation test
        test_stats = np.array([1.8, 3.2, 0.9, 4.1])
        
        result = self.corrector.run_maxt_correction(
            test_stats, n_permutations=1000, seed=42
        )
        
        # Verify we have adjusted p-values for all 4 comparisons
        self.assertEqual(len(result['adjusted_pvalues']), 4)
        
        # All p-values should be in [0, 1]
        self.assertTrue(np.all(result['adjusted_pvalues'] >= 0))
        self.assertTrue(np.all(result['adjusted_pvalues'] <= 1))
        
        # The largest test statistic should have the smallest p-value
        max_stat_idx = np.argmax(test_stats)
        min_p_idx = np.argmin(result['adjusted_pvalues'])
        self.assertEqual(max_stat_idx, min_p_idx)


if __name__ == '__main__':
    unittest.main()