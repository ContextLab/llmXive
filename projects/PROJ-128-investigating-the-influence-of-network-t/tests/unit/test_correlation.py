"""
Unit tests for correlation analysis functions, specifically focusing on
normality checks and Benjamini-Hochberg FDR correction.
"""
import unittest
import numpy as np
import pandas as pd
from scipy.stats import shapiro
from unittest.mock import patch, MagicMock
import warnings

# Import the functions we are testing
# Note: We assume the path is added to sys.path or run from the project root
from code.analysis.correlation import check_normality, benjamini_hochberg_fdr


class TestNormalityCheck(unittest.TestCase):
    """Tests for the check_normality function."""

    def test_normal_data_pearson(self):
        """Test that normally distributed data selects Pearson correlation."""
        # Generate normally distributed data
        np.random.seed(42)
        data = np.random.normal(loc=0, scale=1, size=100)

        # Mock shapiro test to return a high p-value (normal)
        with patch('code.analysis.correlation.shapiro') as mock_shapiro:
            mock_shapiro.return_value = (0.95, 0.85)  # stat, p-value

            corr_type = check_normality(data)
            self.assertEqual(corr_type, 'pearson')

    def test_non_normal_data_spearman(self):
        """Test that non-normally distributed data selects Spearman correlation."""
        # Generate non-normally distributed data (e.g., exponential)
        np.random.seed(42)
        data = np.random.exponential(scale=1.0, size=100)

        # Mock shapiro test to return a low p-value (not normal)
        with patch('code.analysis.correlation.shapiro') as mock_shapiro:
            mock_shapiro.return_value = (0.85, 0.01)  # stat, p-value

            corr_type = check_normality(data)
            self.assertEqual(corr_type, 'spearman')

    def test_small_sample_size(self):
        """Test behavior with small sample size (edge case for Shapiro-Wilk)."""
        np.random.seed(42)
        data = np.random.normal(loc=0, scale=1, size=5)

        with patch('code.analysis.correlation.shapiro') as mock_shapiro:
            # Even if p-value is high, small N might be tricky, but we trust the mock
            mock_shapiro.return_value = (0.90, 0.50)
            corr_type = check_normality(data)
            self.assertEqual(corr_type, 'pearson')

    def test_alpha_threshold(self):
        """Test that the alpha threshold is correctly applied."""
        np.random.seed(42)
        data = np.random.normal(loc=0, scale=1, size=50)

        # Mock exactly at the threshold
        with patch('code.analysis.correlation.shapiro') as mock_shapiro:
            # p-value exactly 0.05 -> should be considered normal (>= alpha)
            mock_shapiro.return_value = (0.95, 0.05)
            corr_type = check_normality(data)
            self.assertEqual(corr_type, 'pearson')

            # p-value just below threshold -> not normal
            mock_shapiro.return_value = (0.95, 0.049)
            corr_type = check_normality(data)
            self.assertEqual(corr_type, 'spearman')


class TestBenjaminiHochbergFDR(unittest.TestCase):
    """Tests for the benjamini_hochberg_fdr function."""

    def test_fdr_correction_basic(self):
        """Test basic FDR correction logic."""
        # Example p-values
        p_values = np.array([0.01, 0.04, 0.03, 0.005, 0.15, 0.20])
        q = 0.05  # FDR threshold

        # Expected calculation (manual verification):
        # Sorted p-values: 0.005, 0.01, 0.03, 0.04, 0.15, 0.20
        # Ranks: 1, 2, 3, 4, 5, 6
        # N = 6
        # Thresholds: (1/6)*0.05=0.0083, (2/6)*0.05=0.0167, (3/6)*0.05=0.025, (4/6)*0.05=0.033, (5/6)*0.05=0.0417, (6/6)*0.05=0.05
        # 0.005 < 0.0083 -> Significant
        # 0.01 < 0.0167 -> Significant
        # 0.03 > 0.025 -> Not significant (and stop)
        # So indices 0, 3 (original) should be significant? Wait, the function returns adjusted p-values or boolean mask?
        # Let's check the function signature logic. Usually returns adjusted p-values or boolean mask.
        # Assuming it returns a boolean mask of significant findings based on q.

        # We need to know the exact return type of benjamini_hochberg_fdr from the source.
        # Based on standard implementations, it often returns (reject, q_value).
        # Let's assume the task expects a boolean mask or a list of booleans.
        
        # Re-reading the function signature in the prompt:
        # public names: ..., benjamini_hochberg_fdr
        # It doesn't specify return type. I will implement the test based on the standard scipy.stats.multipletests or a custom implementation that returns a boolean mask.
        # If the function returns adjusted p-values, the test should check that.
        # Let's assume it returns a boolean array `is_significant`.

        # Since I don't have the source of `code.analysis.correlation` yet (it's a skeleton),
        # I will write the test assuming the standard behavior: returns a boolean array indicating significance.
        # If the implementation returns adjusted p-values, the test will need adjustment.
        
        # Let's assume the function signature is:
        # def benjamini_hochberg_fdr(p_values: np.ndarray, q: float = 0.05) -> np.ndarray:
        # Returns: Boolean array where True means significant after FDR correction.

        # Mocking the actual calculation if it's complex, or testing the logic if simple.
        # Since I am implementing the test for a skeleton, I must assume the function exists.
        # If the function is not implemented, this test will fail, which is expected for TDD.
        
        # Let's create a scenario where we know the outcome.
        # P-values: [0.001, 0.002, 0.01, 0.02, 0.05, 0.1] with q=0.05
        # Sorted: 0.001 (1/6*0.05=0.008), 0.002 (2/6*0.05=0.016), 0.01 (3/6*0.05=0.025), 0.02 (4/6*0.05=0.033), 0.05 (5/6*0.05=0.041), 0.1 (6/6*0.05=0.05)
        # 0.001 < 0.008 -> Sig
        # 0.002 < 0.016 -> Sig
        # 0.01 < 0.025 -> Sig
        # 0.02 < 0.033 -> Sig
        # 0.05 > 0.041 -> Not Sig
        # 0.1 > 0.05 -> Not Sig
        # So first 4 should be True.

        p_values = np.array([0.001, 0.002, 0.01, 0.02, 0.05, 0.1])
        q = 0.05

        try:
            # This might fail if the function is not implemented yet
            result = benjamini_hochberg_fdr(p_values, q)
            
            # Check if result is boolean array
            self.assertIsInstance(result, np.ndarray)
            self.assertTrue(result.dtype == bool)
            
            # Check length
            self.assertEqual(len(result), len(p_values))
            
            # Check specific known outcomes (if the implementation is correct)
            # Note: The order of result should correspond to input order
            # The first 4 are significant in sorted order, but we need to map back to original order.
            # Original: [0.001, 0.002, 0.01, 0.02, 0.05, 0.1] -> All first 4 are significant.
            expected = np.array([True, True, True, True, False, False])
            np.testing.assert_array_equal(result, expected)
            
        except Exception as e:
            # If the function is not implemented, we expect a NotImplementedError or similar
            # But for a TDD test, we write the test first.
            # If the function is a stub, it might raise NotImplementedError.
            # We catch it and mark the test as expected failure? No, in TDD we want the test to fail.
            # So we let it propagate.
            raise e

    def test_fdr_correction_all_significant(self):
        """Test case where all p-values are significant."""
        p_values = np.array([0.001, 0.002, 0.003])
        q = 0.05
        
        try:
            result = benjamini_hochberg_fdr(p_values, q)
            expected = np.array([True, True, True])
            np.testing.assert_array_equal(result, expected)
        except Exception:
            raise

    def test_fdr_correction_none_significant(self):
        """Test case where no p-values are significant."""
        p_values = np.array([0.2, 0.3, 0.4, 0.5])
        q = 0.05
        
        try:
            result = benjamini_hochberg_fdr(p_values, q)
            expected = np.array([False, False, False, False])
            np.testing.assert_array_equal(result, expected)
        except Exception:
            raise

    def test_fdr_correction_with_duplicates(self):
        """Test FDR correction with duplicate p-values."""
        p_values = np.array([0.01, 0.01, 0.01, 0.05])
        q = 0.05
        
        try:
            result = benjamini_hochberg_fdr(p_values, q)
            # All 0.01s should be significant?
            # Sorted: 0.01 (1/4*0.05=0.0125), 0.01 (2/4*0.05=0.025), 0.01 (3/4*0.05=0.0375), 0.05 (4/4*0.05=0.05)
            # 0.01 < 0.0125 -> Sig
            # 0.01 < 0.025 -> Sig
            # 0.01 < 0.0375 -> Sig
            # 0.05 <= 0.05 -> Sig (depending on strict inequality)
            # Assuming <= for significance
            expected = np.array([True, True, True, True])
            np.testing.assert_array_equal(result, expected)
        except Exception:
            raise

    def test_empty_p_values(self):
        """Test FDR correction with empty array."""
        p_values = np.array([])
        q = 0.05
        
        try:
            result = benjamini_hochberg_fdr(p_values, q)
            self.assertEqual(len(result), 0)
        except Exception:
            raise

    def test_single_p_value(self):
        """Test FDR correction with a single p-value."""
        p_values = np.array([0.01])
        q = 0.05
        
        try:
            result = benjamini_hochberg_fdr(p_values, q)
            # 0.01 < 1/1*0.05 = 0.05 -> True
            expected = np.array([True])
            np.testing.assert_array_equal(result, expected)
        except Exception:
            raise

    def test_p_values_out_of_range(self):
        """Test FDR correction with p-values outside [0, 1]."""
        p_values = np.array([-0.1, 1.5])
        q = 0.05
        
        try:
            # The function should handle this, maybe by clipping or raising an error
            # For now, we assume it handles it gracefully or we expect an error
            result = benjamini_hochberg_fdr(p_values, q)
            # If it doesn't raise, check the result
            self.assertIsInstance(result, np.ndarray)
        except (ValueError, IndexError) as e:
            # Expected if the function validates input
            pass
        except Exception:
            # If it raises something else, re-raise
            raise


if __name__ == '__main__':
    unittest.main()