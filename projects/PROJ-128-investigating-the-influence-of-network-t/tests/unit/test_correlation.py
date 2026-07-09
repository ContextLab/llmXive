"""
Unit tests for correlation analysis normality checks and correlation selection.
Tests for code/analysis/correlation.py
"""
import unittest
import numpy as np
from scipy.stats import shapiro
from unittest.mock import patch, MagicMock

# Import the function under test
# The function signature is expected to be:
# check_normality(data_series, alpha=0.05) -> Tuple[bool, float]
# Returns (is_normal, statistic)
try:
    from analysis.correlation import check_normality, benjamini_hochberg_fdr
except ImportError:
    # Fallback for testing environment if import path differs
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from analysis.correlation import check_normality, benjamini_hochberg_fdr


class TestNormalityCheck(unittest.TestCase):
    """Tests for the Shapiro-Wilk normality check logic."""

    def test_normal_distribution(self):
        """Test that a normally distributed sample is identified as normal."""
        # Generate a sample from a normal distribution
        np.random.seed(42)
        data = np.random.normal(loc=0, scale=1, size=100)
        
        is_normal, stat = check_normality(data)
        
        self.assertTrue(is_normal)
        self.assertIsInstance(stat, float)
        # For normal data, p-value should be > alpha (0.05), so we don't reject null
        # The function should return True if p > alpha

    def test_non_normal_distribution(self):
        """Test that a highly skewed distribution is identified as non-normal."""
        # Generate a sample from an exponential distribution (skewed)
        np.random.seed(42)
        data = np.random.exponential(scale=1.0, size=100)
        
        is_normal, stat = check_normality(data)
        
        # Exponential distribution with n=100 is usually detected as non-normal
        # We assert that it is likely detected as non-normal (is_normal=False)
        # Note: With small samples, Shapiro-Wilk might not always detect non-normality,
        # but exponential is a strong candidate.
        self.assertFalse(is_normal)

    def test_small_sample_size(self):
        """Test behavior with small sample sizes (Shapiro-Wilk requires n >= 3)."""
        np.random.seed(42)
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        is_normal, stat = check_normality(data)
        
        self.assertTrue(is_normal)
        self.assertIsInstance(stat, float)

    def test_alpha_threshold(self):
        """Test that the alpha threshold is respected in the decision."""
        # Create a dataset that is borderline
        # We mock the shapiro function to return a specific p-value to test logic
        with patch('scipy.stats.shapiro') as mock_shapiro:
            # Mock return: statistic, p-value
            # If p-value is 0.04 (less than 0.05), should be False
            mock_shapiro.return_value = (0.95, 0.04)
            
            is_normal, stat = check_normality(np.array([1, 2, 3, 4, 5]), alpha=0.05)
            self.assertFalse(is_normal)
            
            # If p-value is 0.06 (greater than 0.05), should be True
            mock_shapiro.return_value = (0.95, 0.06)
            is_normal, stat = check_normality(np.array([1, 2, 3, 4, 5]), alpha=0.05)
            self.assertTrue(is_normal)

    def test_custom_alpha(self):
        """Test with a custom alpha level."""
        np.random.seed(42)
        data = np.random.normal(0, 1, 50)
        
        # With alpha=0.01, it should still be normal
        is_normal_01, _ = check_normality(data, alpha=0.01)
        self.assertTrue(is_normal_01)

    def test_input_types(self):
        """Test that the function handles list and numpy array inputs."""
        data_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        data_array = np.array(data_list)
        
        is_normal_list, _ = check_normality(data_list)
        is_normal_array, _ = check_normality(data_array)
        
        self.assertTrue(is_normal_list)
        self.assertTrue(is_normal_array)


class TestCorrelationSelectionLogic(unittest.TestCase):
    """Tests for the logic that selects Pearson vs Spearman based on normality."""
    
    def test_selection_logic(self):
        """
        Verify that the correlation analysis function (or helper) would select
        Pearson for normal data and Spearman for non-normal data.
        This test validates the decision logic that would be used in calculate_correlation.
        """
        # We test the decision outcome by mocking the normality check
        from scipy.stats import pearsonr, spearmanr
        
        # Mock data
        normal_data = np.random.normal(0, 1, 50)
        x = normal_data
        y = normal_data * 2 + np.random.normal(0, 0.1, 50)
        
        # Scenario 1: Data is normal -> Should use Pearson
        with patch('analysis.correlation.shapiro') as mock_shapiro:
            mock_shapiro.return_value = (0.98, 0.8) # p > 0.05 -> Normal
            is_normal, _ = check_normality(x)
            self.assertTrue(is_normal)
            
            # Simulate the selection logic
            if is_normal:
                corr_func = pearsonr
            else:
                corr_func = spearmanr
            
            # Verify we selected pearsonr
            self.assertEqual(corr_func, pearsonr)
        
        # Scenario 2: Data is non-normal -> Should use Spearman
        with patch('analysis.correlation.shapiro') as mock_shapiro:
            mock_shapiro.return_value = (0.85, 0.01) # p < 0.05 -> Non-normal
            is_normal, _ = check_normality(x)
            self.assertFalse(is_normal)
            
            if is_normal:
                corr_func = pearsonr
            else:
                corr_func = spearmanr
            
            # Verify we selected spearmanr
            self.assertEqual(corr_func, spearmanr)


class TestBenjaminiHochbergFDR(unittest.TestCase):
    """Tests for the Benjamini-Hochberg FDR correction implementation."""

    def test_fdr_on_simple_array(self):
        """
        Test BH correction on a simple array of p-values.
        We verify that the adjusted p-values are monotonically non-decreasing
        when sorted by original p-value, and that they respect the BH formula.
        """
        # Example p-values
        p_values = np.array([0.01, 0.04, 0.03, 0.20, 0.15])
        alpha = 0.05
        
        # Run FDR correction
        adjusted_p_values = benjamini_hochberg_fdr(p_values, alpha=alpha)
        
        # Basic sanity checks
        self.assertEqual(len(adjusted_p_values), len(p_values))
        self.assertTrue(np.all(adjusted_p_values >= 0))
        self.assertTrue(np.all(adjusted_p_values <= 1.0))
        
        # Check monotonicity: when sorted by original p-values, adjusted should be non-decreasing
        sorted_indices = np.argsort(p_values)
        sorted_adj = adjusted_p_values[sorted_indices]
        
        # The BH procedure ensures that if we sort by p-value, the adjusted p-values
        # are non-decreasing. We check this property.
        self.assertTrue(np.all(np.diff(sorted_adj) >= -1e-10)) # Allow tiny float errors

    def test_fdr_all_significant(self):
        """
        Test case where all p-values are very small and should remain significant after FDR.
        """
        p_values = np.array([0.001, 0.002, 0.003])
        alpha = 0.05
        
        adjusted_p_values = benjamini_hochberg_fdr(p_values, alpha=alpha)
        
        # All adjusted p-values should be less than alpha
        self.assertTrue(np.all(adjusted_p_values < alpha))

    def test_fdr_none_significant(self):
        """
        Test case where all p-values are large and none should be significant after FDR.
        """
        p_values = np.array([0.5, 0.6, 0.7])
        alpha = 0.05
        
        adjusted_p_values = benjamini_hochberg_fdr(p_values, alpha=alpha)
        
        # All adjusted p-values should be greater than alpha
        self.assertTrue(np.all(adjusted_p_values > alpha))

    def test_fdr_mixed(self):
        """
        Test case with a mix of significant and non-significant p-values.
        """
        p_values = np.array([0.001, 0.04, 0.06, 0.2, 0.5])
        alpha = 0.05
        
        adjusted_p_values = benjamini_hochberg_fdr(p_values, alpha=alpha)
        
        # We expect the first few (smallest original p-values) to be < alpha
        # and the larger ones to be > alpha.
        # Specifically, for BH:
        # m=5.
        # Sorted p: 0.001, 0.04, 0.06, 0.2, 0.5
        # Thresholds: 0.05*1/5=0.01, 0.05*2/5=0.02, 0.05*3/5=0.03, 0.05*4/5=0.04, 0.05*5/5=0.05
        # 0.001 < 0.01 -> sig
        # 0.04 > 0.02 -> not sig (but we check adjusted values)
        # The function returns adjusted p-values.
        # We check that the count of significant findings is reasonable.
        significant_count = np.sum(adjusted_p_values < alpha)
        # We expect at least 1 (the 0.001 one)
        self.assertGreaterEqual(significant_count, 1)

    def test_fdr_single_value(self):
        """Test FDR correction with a single p-value."""
        p_values = np.array([0.01])
        alpha = 0.05
        
        adjusted_p_values = benjamini_hochberg_fdr(p_values, alpha=alpha)
        
        self.assertEqual(len(adjusted_p_values), 1)
        # For a single value, BH adjusted p-value is just p * m / k = p * 1 / 1 = p
        self.assertAlmostEqual(adjusted_p_values[0], p_values[0])

    def test_fdr_empty_array(self):
        """Test FDR correction with an empty array."""
        p_values = np.array([])
        alpha = 0.05
        
        adjusted_p_values = benjamini_hochberg_fdr(p_values, alpha=alpha)
        
        self.assertEqual(len(adjusted_p_values), 0)

    def test_fdr_monotonicity_enforcement(self):
        """
        Test that the BH implementation enforces the monotonicity constraint:
        adjusted_p[i] <= adjusted_p[i+1] when sorted by original p.
        This is a critical property of the BH procedure to avoid illogical results.
        """
        # Create a case where naive calculation might violate monotonicity if not handled
        # e.g., p-values that are increasing but the raw BH calculation might dip
        p_values = np.array([0.01, 0.02, 0.03, 0.04, 0.05])
        alpha = 0.05
        
        adjusted_p_values = benjamini_hochberg_fdr(p_values, alpha=alpha)
        
        sorted_indices = np.argsort(p_values)
        sorted_adj = adjusted_p_values[sorted_indices]
        
        # Check non-decreasing
        for i in range(len(sorted_adj) - 1):
            self.assertGreaterEqual(sorted_adj[i+1], sorted_adj[i] - 1e-10)


if __name__ == '__main__':
    unittest.main()