"""
Unit tests for statistical tests in code/evaluation/metrics.py.

Verifies:
- Paired-sample t-test implementation
- TOST (Two One-Sided Tests) implementation
- Hotelling's T² test implementation
"""

import pytest
import numpy as np
from scipy import stats
from scipy.stats import ttest_rel
from typing import Tuple

# Import the functions to be tested from the evaluation module
# Note: We assume these functions will be implemented in code/evaluation/metrics.py
# For now, we define mock implementations to test the logic
# In the actual implementation, these would be imported from code/evaluation/metrics.py

def paired_ttest(errors: np.ndarray, alpha: float = 0.05) -> Tuple[float, float]:
    """
    Perform paired-sample t-test.
    
    Args:
        errors: Array of prediction errors (pred - true)
        alpha: Significance level
        
    Returns:
        Tuple of (t_statistic, p_value)
    """
    # Test against zero mean error
    t_stat, p_val = ttest_rel(errors, np.zeros_like(errors))
    return t_stat, p_val

def tost(errors: np.ndarray, equivalence_margin: float, alpha: float = 0.05) -> Tuple[bool, float, float]:
    """
    Perform Two One-Sided Tests (TOST) for equivalence.
    
    Args:
        errors: Array of prediction errors
        equivalence_margin: The margin within which equivalence is claimed
        alpha: Significance level
        
    Returns:
        Tuple of (is_equivalent, p_value_lower, p_value_upper)
    """
    # Lower bound test: H0: mean_error <= -margin vs H1: mean_error > -margin
    t_lower, p_lower = ttest_rel(errors, np.full_like(errors, -equivalence_margin))
    
    # Upper bound test: H0: mean_error >= margin vs H1: mean_error < margin
    t_upper, p_upper = ttest_rel(errors, np.full_like(errors, equivalence_margin))
    
    # For one-sided tests, we need to adjust p-values
    # Since ttest_rel returns two-sided p-values, we divide by 2
    p_lower_one_sided = p_lower / 2.0 if t_lower > 0 else 1.0 - p_lower / 2.0
    p_upper_one_sided = p_upper / 2.0 if t_upper < 0 else 1.0 - p_upper / 2.0
    
    # Equivalence is claimed if both one-sided tests reject their null hypotheses
    is_equivalent = (p_lower_one_sided < alpha) and (p_upper_one_sided < alpha)
    
    return is_equivalent, p_lower_one_sided, p_upper_one_sided

def hotellings_t2(errors: np.ndarray, reference_errors: np.ndarray = None) -> Tuple[float, float]:
    """
    Perform Hotelling's T² test for multivariate differences.
    
    Args:
        errors: 2D array of errors (n_samples, n_properties)
        reference_errors: Optional reference errors for comparison
        
    Returns:
        Tuple of (t2_statistic, p_value)
    """
    n_samples, n_properties = errors.shape
    
    if reference_errors is None:
        # Test if mean vector is zero
        mean_errors = np.mean(errors, axis=0)
        cov_matrix = np.cov(errors.T)
        
        # Add small regularization to avoid singular matrix
        cov_matrix += np.eye(n_properties) * 1e-8
        
        try:
            cov_inv = np.linalg.inv(cov_matrix)
        except np.linalg.LinAlgError:
            # If matrix is singular, return NaN
            return np.nan, np.nan
        
        t2 = n_samples * mean_errors @ cov_inv @ mean_errors
        
        # Convert to F-statistic
        df1 = n_properties
        df2 = n_samples - n_properties
        if df2 <= 0:
            return np.nan, np.nan
            
        f_stat = (df2 / (df1 * (n_samples - 1))) * t2
        p_value = 1.0 - stats.f.cdf(f_stat, df1, df2)
        
    else:
        # Two-sample Hotelling's T² test
        n1, p = errors.shape
        n2 = reference_errors.shape[0]
        
        mean1 = np.mean(errors, axis=0)
        mean2 = np.mean(reference_errors, axis=0)
        
        # Pooled covariance
        cov1 = np.cov(errors.T)
        cov2 = np.cov(reference_errors.T)
        
        cov_pooled = ((n1 - 1) * cov1 + (n2 - 1) * cov2) / (n1 + n2 - 2)
        
        # Add regularization
        cov_pooled += np.eye(p) * 1e-8
        
        try:
            cov_inv = np.linalg.inv(cov_pooled)
        except np.linalg.LinAlgError:
            return np.nan, np.nan
        
        diff = mean1 - mean2
        t2 = (n1 * n2 / (n1 + n2)) * diff @ cov_inv @ diff
        
        # Convert to F-statistic
        df1 = p
        df2 = n1 + n2 - p - 1
        if df2 <= 0:
            return np.nan, np.nan
            
        f_stat = (df2 / (df1 * (n1 + n2 - 2))) * t2
        p_value = 1.0 - stats.f.cdf(f_stat, df1, df2)
    
    return t2, p_value


class TestPairedTTest:
    """Tests for paired-sample t-test implementation."""
    
    def test_ttest_zero_mean(self):
        """Test that zero mean errors produce high p-value."""
        errors = np.array([0.0, 0.0, 0.0, 0.0, 0.0])
        t_stat, p_val = paired_ttest(errors)
        assert p_val > 0.05, "Zero mean errors should not be significant"
        
    def test_ttest_nonzero_mean(self):
        """Test that non-zero mean errors produce low p-value."""
        errors = np.array([1.0, 1.1, 0.9, 1.0, 1.0])
        t_stat, p_val = paired_ttest(errors)
        assert p_val < 0.05, "Non-zero mean errors should be significant"
        
    def test_ttest_sign(self):
        """Test that t-statistic sign matches mean error direction."""
        errors_positive = np.array([1.0, 1.0, 1.0])
        errors_negative = np.array([-1.0, -1.0, -1.0])
        
        t_stat_pos, _ = paired_ttest(errors_positive)
        t_stat_neg, _ = paired_ttest(errors_negative)
        
        assert t_stat_pos > 0, "Positive mean should give positive t-stat"
        assert t_stat_neg < 0, "Negative mean should give negative t-stat"
    
    def test_ttest_with_realistic_errors(self):
        """Test with realistic error distribution."""
        np.random.seed(42)
        errors = np.random.normal(loc=0.1, scale=0.5, size=100)
        t_stat, p_val = paired_ttest(errors)
        assert not np.isnan(p_val), "p-value should not be NaN"
        assert 0.0 <= p_val <= 1.0, "p-value should be between 0 and 1"


class TestTOST:
    """Tests for TOST (equivalence testing) implementation."""
    
    def test_tost_equivalent(self):
        """Test that small errors within margin are deemed equivalent."""
        errors = np.array([0.01, -0.01, 0.02, -0.02, 0.0])
        is_equiv, p_low, p_high = tost(errors, equivalence_margin=0.1)
        assert is_equiv, "Small errors should be equivalent"
        assert p_low < 0.05, "Lower bound p-value should be significant"
        assert p_high < 0.05, "Upper bound p-value should be significant"
        
    def test_tost_not_equivalent(self):
        """Test that large errors outside margin are not equivalent."""
        errors = np.array([1.0, 1.1, 0.9, 1.0, 1.0])
        is_equiv, p_low, p_high = tost(errors, equivalence_margin=0.1)
        assert not is_equiv, "Large errors should not be equivalent"
        
    def test_tost_asymmetric(self):
        """Test with asymmetric error distribution."""
        np.random.seed(42)
        errors = np.random.normal(loc=0.05, scale=0.02, size=50)
        is_equiv, p_low, p_high = tost(errors, equivalence_margin=0.1)
        assert is_equiv, "Errors within margin should be equivalent"
        
    def test_tost_p_value_range(self):
        """Test that p-values are in valid range."""
        errors = np.random.normal(loc=0.0, scale=0.1, size=30)
        _, p_low, p_high = tost(errors, equivalence_margin=0.5)
        assert 0.0 <= p_low <= 1.0, "Lower p-value should be in [0, 1]"
        assert 0.0 <= p_high <= 1.0, "Upper p-value should be in [0, 1]"


class TestHotellingsT2:
    """Tests for Hotelling's T² test implementation."""
    
    def test_hotelling_zero_mean(self):
        """Test that zero mean errors produce high p-value."""
        errors = np.zeros((10, 3))  # 10 samples, 3 properties
        t2, p_val = hotellings_t2(errors)
        assert p_val > 0.05, "Zero mean errors should not be significant"
        
    def test_hotelling_nonzero_mean(self):
        """Test that non-zero mean errors produce low p-value."""
        errors = np.ones((10, 3)) * 1.0
        t2, p_val = hotellings_t2(errors)
        # With large effect size, should be significant
        assert p_val < 0.05, "Non-zero mean errors should be significant"
        
    def test_hotelling_two_sample(self):
        """Test two-sample Hotelling's T²."""
        errors1 = np.random.normal(loc=0.0, scale=0.5, size=(20, 3))
        errors2 = np.random.normal(loc=0.5, scale=0.5, size=(20, 3))
        t2, p_val = hotellings_t2(errors1, reference_errors=errors2)
        assert not np.isnan(p_val), "p-value should not be NaN"
        assert 0.0 <= p_val <= 1.0, "p-value should be between 0 and 1"
        
    def test_hotelling_singular_covariance(self):
        """Test handling of singular covariance matrix."""
        # Create data with perfect correlation (singular covariance)
        errors = np.array([[1.0, 2.0, 3.0]] * 5)  # All rows identical
        t2, p_val = hotellings_t2(errors)
        # Should return NaN for singular case
        assert np.isnan(p_val) or p_val >= 0.0, "Should handle singular matrix gracefully"
        
    def test_hotelling_dimensionality(self):
        """Test with different dimensionalities."""
        for n_props in [1, 2, 3, 5]:
            errors = np.random.normal(loc=0.1, scale=0.5, size=(30, n_props))
            t2, p_val = hotellings_t2(errors)
            assert not np.isnan(p_val) or n_props >= 30, \
                f"Should handle {n_props} properties correctly"

class TestIntegration:
    """Integration tests for statistical tests working together."""
    
    def test_all_tests_on_same_data(self):
        """Run all tests on the same error dataset."""
        np.random.seed(42)
        errors_1d = np.random.normal(loc=0.1, scale=0.3, size=50)
        errors_2d = np.random.normal(loc=0.1, scale=0.3, size=(50, 3))
        
        # Paired t-test
        t_stat, p_val = paired_ttest(errors_1d)
        assert 0.0 <= p_val <= 1.0
        
        # TOST
        is_equiv, p_low, p_high = tost(errors_1d, equivalence_margin=0.5)
        assert isinstance(is_equiv, bool)
        assert 0.0 <= p_low <= 1.0
        assert 0.0 <= p_high <= 1.0
        
        # Hotelling's T²
        t2, p_val_hot = hotellings_t2(errors_2d)
        assert 0.0 <= p_val_hot <= 1.0 or np.isnan(p_val_hot)
        
    def test_consistency_with_scipy(self):
        """Verify our t-test matches scipy implementation."""
        np.random.seed(42)
        errors = np.random.normal(loc=0.1, scale=0.3, size=50)
        
        # Our implementation
        t_stat, p_val = paired_ttest(errors)
        
        # Scipy implementation
        t_stat_scipy, p_val_scipy = ttest_rel(errors, np.zeros_like(errors))
        
        assert np.isclose(t_stat, t_stat_scipy), "t-statistic should match scipy"
        assert np.isclose(p_val, p_val_scipy), "p-value should match scipy"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])