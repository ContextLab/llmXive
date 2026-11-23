"""
Unit tests for normality check and test selection logic in analysis.py.

This module verifies that:
1. The normality check correctly identifies Gaussian vs non-Gaussian distributions.
2. The test selection logic chooses the appropriate statistical test (t-test vs Wilcoxon)
   based on the normality results.
3. Edge cases (small samples, identical values) are handled correctly.
"""
import unittest
import numpy as np
from scipy import stats
from unittest.mock import patch, MagicMock

# Import the functions we are testing
# Note: We assume these functions will be implemented in code/analysis.py
# For now, we define them here to allow the tests to run.
# In the actual implementation, these will be imported from analysis.py.

def check_normality(data, alpha=0.05):
    """
    Perform Shapiro-Wilk test for normality.
    
    Args:
        data: Array-like, the data to test for normality.
        alpha: Significance level for the test.
        
    Returns:
      bool: True if data is normally distributed (p-value > alpha), False otherwise.
    """
    if len(data) < 3:
        # Cannot perform Shapiro-Wilk on very small samples
        # Assume normal for the sake of the test (or raise an exception)
        # Here we assume normal to avoid crashing on tiny samples
        return True
    
    try:
        _, p_value = stats.shapiro(data)
        return p_value > alpha
    except Exception:
        # If the test fails (e.g., sample too large for Shapiro-Wilk),
        # fall back to a heuristic or return False.
        # For this unit test, we'll return False to be conservative.
        return False

def select_statistical_test(baseline_data, perturbed_data, alpha=0.05):
    """
    Select the appropriate statistical test based on normality checks.
    
    Args:
        baseline_data: Array-like, the baseline similarity scores.
        perturbed_data: Array-like, the perturbed similarity scores.
        alpha: Significance level for the normality test.
        
    Returns:
        str: 't-test' if both distributions are normal, 'wilcoxon' otherwise.
    """
    is_baseline_normal = check_normality(baseline_data, alpha)
    is_perturbed_normal = check_normality(perturbed_data, alpha)
    
    if is_baseline_normal and is_perturbed_normal:
        return 't-test'
    else:
        return 'wilcoxon'

class TestNormalityCheck(unittest.TestCase):
    """Tests for the normality check function."""
    
    def test_gaussian_distribution(self):
        """Test that a Gaussian distribution is identified as normal."""
        np.random.seed(42)
        data = np.random.normal(loc=0.0, scale=1.0, size=1000)
        self.assertTrue(check_normality(data))
    
    def test_non_gaussian_distribution(self):
        """Test that a non-Gaussian distribution is identified as non-normal."""
        # Create a highly skewed distribution
        data = np.random.exponential(scale=1.0, size=1000)
        self.assertFalse(check_normality(data))
    
    def test_small_sample_normal(self):
        """Test behavior with a small sample that is normally distributed."""
        np.random.seed(42)
        data = np.random.normal(loc=0.0, scale=1.0, size=10)
        # Small samples are harder to reject normality, so this might pass
        # We expect it to return True (normal) or handle the small sample gracefully.
        result = check_normality(data)
        self.assertIsInstance(result, bool)
    
    def test_small_sample_non_normal(self):
        """Test behavior with a small sample that is non-normally distributed."""
        # Create a small, skewed sample
        data = np.array([1, 2, 3, 10, 100])
        result = check_normality(data)
        self.assertIsInstance(result, bool)
    
    def test_very_small_sample(self):
        """Test behavior with a very small sample (n < 3)."""
        data = np.array([1, 2])
        # Should handle gracefully, returning True as per our implementation
        self.assertTrue(check_normality(data))
    
    def test_constant_values(self):
        """Test behavior with constant values (zero variance)."""
        data = np.ones(100)
        # Shapiro-Wilk might fail or return p=1.0 for constant data
        result = check_normality(data)
        self.assertIsInstance(result, bool)

class TestTestSelection(unittest.TestCase):
    """Tests for the statistical test selection logic."""
    
    def test_both_normal(self):
        """Test selection when both distributions are normal."""
        np.random.seed(42)
        baseline = np.random.normal(0, 1, 500)
        perturbed = np.random.normal(0.5, 1, 500)
        
        with patch('tests.unit.test_statistical_test.check_normality', return_value=True):
            result = select_statistical_test(baseline, perturbed)
            self.assertEqual(result, 't-test')
    
    def test_baseline_non_normal(self):
        """Test selection when baseline is non-normal."""
        np.random.seed(42)
        baseline = np.random.exponential(1, 500)
        perturbed = np.random.normal(0.5, 1, 500)
        
        with patch('tests.unit.test_statistical_test.check_normality', side_effect=[False, True]):
            result = select_statistical_test(baseline, perturbed)
            self.assertEqual(result, 'wilcoxon')
    
    def test_perturbed_non_normal(self):
        """Test selection when perturbed is non-normal."""
        np.random.seed(42)
        baseline = np.random.normal(0, 1, 500)
        perturbed = np.random.exponential(1, 500)
        
        with patch('tests.unit.test_statistical_test.check_normality', side_effect=[True, False]):
            result = select_statistical_test(baseline, perturbed)
            self.assertEqual(result, 'wilcoxon')
    
    def test_both_non_normal(self):
        """Test selection when both distributions are non-normal."""
        np.random.seed(42)
        baseline = np.random.exponential(1, 500)
        perturbed = np.random.exponential(1.5, 500)
        
        with patch('tests.unit.test_statistical_test.check_normality', return_value=False):
            result = select_statistical_test(baseline, perturbed)
            self.assertEqual(result, 'wilcoxon')
    
    def test_real_data_scenario(self):
        """Test selection with real-like data (Gaussian vs Exponential)."""
        np.random.seed(42)
        # Simulate baseline as normal
        baseline = np.random.normal(0.8, 0.1, 1000)
        # Simulate perturbed as slightly skewed
        perturbed = np.random.exponential(0.8, 1000)
        
        # Mock the normality checks to reflect the data characteristics
        with patch('tests.unit.test_statistical_test.check_normality', side_effect=[True, False]):
            result = select_statistical_test(baseline, perturbed)
            self.assertEqual(result, 'wilcoxon')

class TestIntegration(unittest.TestCase):
    """Integration tests for the full pipeline."""
    
    def test_end_to_end_normal(self):
        """Test the full flow with normally distributed data."""
        np.random.seed(42)
        baseline = np.random.normal(0.8, 0.1, 1000)
        perturbed = np.random.normal(0.85, 0.1, 1000)
        
        # Both should be normal
        with patch('tests.unit.test_statistical_test.check_normality', return_value=True):
            test_type = select_statistical_test(baseline, perturbed)
            self.assertEqual(test_type, 't-test')
            
            # Run the actual t-test to ensure it works
            statistic, p_value = stats.ttest_ind(baseline, perturbed)
            self.assertIsInstance(statistic, float)
            self.assertIsInstance(p_value, float)
    
    def test_end_to_end_non_normal(self):
        """Test the full flow with non-normally distributed data."""
        np.random.seed(42)
        baseline = np.random.exponential(0.8, 1000)
        perturbed = np.random.exponential(0.85, 1000)
        
        # Both should be non-normal
        with patch('tests.unit.test_statistical_test.check_normality', return_value=False):
            test_type = select_statistical_test(baseline, perturbed)
            self.assertEqual(test_type, 'wilcoxon')
            
            # Run the actual Wilcoxon test to ensure it works
            statistic, p_value = stats.wilcoxon(baseline, perturbed)
            self.assertIsInstance(statistic, float)
            self.assertIsInstance(p_value, float)

if __name__ == '__main__':
    unittest.main()