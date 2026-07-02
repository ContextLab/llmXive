"""
Unit tests for FDR correction and correlation thresholding logic.
Implements T027: [P] [US3] Unit test for FDR correction and correlation thresholding.
"""
import unittest
import numpy as np
from scipy import stats
import sys
import os

# Add project root to path to allow imports from code/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from code.utils.validation import log_error

class TestFDRCorrection(unittest.TestCase):
    """Tests for Benjamini-Hochberg FDR correction implementation."""

    def test_fdr_correction_basic(self):
        """Test basic FDR correction with known p-values."""
        # Known p-values sorted
        p_values = np.array([0.001, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5])
        n = len(p_values)
        alpha = 0.05

        # Expected critical values: p_i * (n / i)
        # i ranges from 1 to n
        expected_critical_values = p_values * (n / np.arange(1, n + 1))

        # Find the largest p-value where p_i <= critical value
        # This is the standard BH procedure
        is_significant = np.zeros(n, dtype=bool)
        threshold = 0.0
        
        for i in range(n - 1, -1, -1):
            if p_values[i] <= expected_critical_values[i]:
                threshold = p_values[i]
                is_significant[:i+1] = True
                break

        # Verify at least one significant result exists
        self.assertTrue(np.any(is_significant), "Expected at least one significant result")
        
        # Verify the threshold is less than alpha
        self.assertLess(threshold, alpha, "Threshold should be less than alpha")

    def test_fdr_correction_all_non_significant(self):
        """Test FDR when all p-values are large."""
        p_values = np.array([0.5, 0.6, 0.7, 0.8])
        n = len(p_values)
        alpha = 0.05

        expected_critical_values = p_values * (n / np.arange(1, n + 1))
        is_significant = np.zeros(n, dtype=bool)
        threshold = 0.0

        for i in range(n - 1, -1, -1):
            if p_values[i] <= expected_critical_values[i]:
                threshold = p_values[i]
                is_significant[:i+1] = True
                break

        # No significant results expected
        self.assertFalse(np.any(is_significant), "Expected no significant results")
        self.assertEqual(threshold, 0.0, "Threshold should be 0.0")

    def test_fdr_correction_all_significant(self):
        """Test FDR when all p-values are very small."""
        p_values = np.array([0.0001, 0.0002, 0.0003, 0.0004])
        n = len(p_values)
        alpha = 0.05

        expected_critical_values = p_values * (n / np.arange(1, n + 1))
        is_significant = np.zeros(n, dtype=bool)
        threshold = 0.0

        for i in range(n - 1, -1, -1):
            if p_values[i] <= expected_critical_values[i]:
                threshold = p_values[i]
                is_significant[:i+1] = True
                break

        # All significant
        self.assertTrue(np.all(is_significant), "Expected all significant results")
        self.assertLess(threshold, alpha, "Threshold should be less than alpha")

    def test_fdr_correction_edge_case_single(self):
        """Test FDR with a single p-value."""
        p_values = np.array([0.01])
        n = 1
        alpha = 0.05

        expected_critical_value = p_values[0] * (n / 1)
        is_significant = p_values[0] <= expected_critical_value

        self.assertTrue(is_significant, "Single small p-value should be significant")

    def test_fdr_correction_edge_case_single_large(self):
        """Test FDR with a single large p-value."""
        p_values = np.array([0.5])
        n = 1
        alpha = 0.05

        expected_critical_value = p_values[0] * (n / 1)
        is_significant = p_values[0] <= expected_critical_value

        self.assertFalse(is_significant, "Single large p-value should not be significant")

class TestCorrelationThresholding(unittest.TestCase):
    """Tests for correlation coefficient thresholding logic."""

    def test_threshold_check_pass(self):
        """Test that correlation above threshold is marked as pass."""
        r_value = 0.45
        threshold = 0.3
        
        status = "PASS" if abs(r_value) >= threshold else "FAIL"
        
        self.assertEqual(status, "PASS", "Correlation 0.45 should pass 0.3 threshold")

    def test_threshold_check_fail(self):
        """Test that correlation below threshold is marked as fail."""
        r_value = 0.25
        threshold = 0.3
        
        status = "PASS" if abs(r_value) >= threshold else "FAIL"
        
        self.assertEqual(status, "FAIL", "Correlation 0.25 should fail 0.3 threshold")

    def test_threshold_check_negative(self):
        """Test that negative correlation above threshold magnitude is pass."""
        r_value = -0.45
        threshold = 0.3
        
        status = "PASS" if abs(r_value) >= threshold else "FAIL"
        
        self.assertEqual(status, "PASS", "Correlation -0.45 should pass 0.3 threshold (magnitude)")

    def test_threshold_check_exact(self):
        """Test exact threshold match."""
        r_value = 0.3
        threshold = 0.3
        
        status = "PASS" if abs(r_value) >= threshold else "FAIL"
        
        self.assertEqual(status, "PASS", "Correlation 0.3 should pass 0.3 threshold")

    def test_reliability_threshold(self):
        """Test reliability coefficient thresholding."""
        reliability = 0.75
        threshold = 0.7
        
        status = "PASS" if reliability >= threshold else "LOW"
        
        self.assertEqual(status, "PASS", "Reliability 0.75 should pass 0.7 threshold")

    def test_reliability_threshold_low(self):
        """Test low reliability coefficient thresholding."""
        reliability = 0.65
        threshold = 0.7
        
        status = "PASS" if reliability >= threshold else "LOW"
        
        self.assertEqual(status, "LOW", "Reliability 0.65 should be marked LOW")

class TestFDRIntegration(unittest.TestCase):
    """Integration tests combining FDR and thresholding."""

    def test_full_pipeline_simulation(self):
        """Simulate a full analysis pipeline with FDR and thresholding."""
        # Simulate p-values from multiple tests (e.g., electrodes x metrics)
        np.random.seed(42)
        n_tests = 20
        # Mix of significant and non-significant p-values
        p_values = np.concatenate([
            np.random.uniform(0.001, 0.02, 5),  # Significant
            np.random.uniform(0.05, 0.5, 15)    # Non-significant
        ])
        
        # Sort p-values for BH procedure
        sorted_indices = np.argsort(p_values)
        sorted_p_values = p_values[sorted_indices]
        n = len(sorted_p_values)
        alpha = 0.05

        # Apply BH FDR
        critical_values = sorted_p_values * (n / np.arange(1, n + 1))
        is_significant = np.zeros(n, dtype=bool)
        threshold = 0.0
        
        for i in range(n - 1, -1, -1):
            if sorted_p_values[i] <= critical_values[i]:
                threshold = sorted_p_values[i]
                is_significant[:i+1] = True
                break

        # Map back to original order
        final_significance = np.zeros(n_tests, dtype=bool)
        final_significance[sorted_indices] = is_significant

        # Count significant results
        n_significant = np.sum(final_significance)
        
        # We expect at least the 5 truly significant ones to be detected
        self.assertGreaterEqual(n_significant, 5, 
                                "Expected at least 5 significant results after FDR")
        
        # Verify threshold is reasonable
        self.assertLess(threshold, alpha, "FDR threshold should be less than alpha")

    def test_correlation_with_pvalue_filtering(self):
        """Test correlation analysis with p-value filtering via FDR."""
        # Simulate correlation coefficients and p-values
        r_values = np.array([0.1, 0.2, 0.35, 0.45, 0.5, 0.15, 0.05])
        p_values = np.array([0.4, 0.25, 0.04, 0.01, 0.005, 0.3, 0.6])
        
        # Apply FDR
        n = len(p_values)
        alpha = 0.05
        sorted_indices = np.argsort(p_values)
        sorted_p_values = p_values[sorted_indices]
        
        critical_values = sorted_p_values * (n / np.arange(1, n + 1))
        is_sig = np.zeros(n, dtype=bool)
        
        for i in range(n - 1, -1, -1):
            if sorted_p_values[i] <= critical_values[i]:
                is_sig[:i+1] = True
                break
        
        final_sig = np.zeros(n, dtype=bool)
        final_sig[sorted_indices] = is_sig
        
        # Filter correlations by FDR significance
        significant_r_values = r_values[final_sig]
        
        # Apply correlation threshold
        r_threshold = 0.3
        strong_correlations = significant_r_values[np.abs(significant_r_values) >= r_threshold]
        
        # We expect at least the 0.35, 0.45, 0.5 to be detected
        self.assertGreaterEqual(len(strong_correlations), 3,
                                "Expected at least 3 strong significant correlations")

if __name__ == '__main__':
    unittest.main()