import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Ensure project root is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from analysis.metrics import calculate_empirical_error_rate, calculate_confidence_interval


class TestEmpiricalErrorRate:
    """Contract tests for empirical error rate calculation."""

    def test_empirical_error_rate_basic(self):
        """Test that error rate is calculated as count < alpha / total."""
        p_values = np.array([0.01, 0.02, 0.03, 0.04, 0.06, 0.10, 0.20, 0.50])
        alpha = 0.05
        total_tests = len(p_values)
        expected_rejections = 3  # 0.01, 0.02, 0.03, 0.04 are < 0.05 -> wait, 4
        # Actually: 0.01, 0.02, 0.03, 0.04 are < 0.05 -> 4 rejections
        # 0.06, 0.10, 0.20, 0.50 are >= 0.05 -> 4 non-rejections
        
        rate, count = calculate_empirical_error_rate(p_values, alpha)
        
        assert count == 4, f"Expected 4 rejections, got {count}"
        assert abs(rate - 0.5) < 1e-9, f"Expected rate 0.5, got {rate}"

    def test_empirical_error_rate_no_rejections(self):
        """Test when no p-values are below alpha."""
        p_values = np.array([0.10, 0.20, 0.30, 0.40, 0.50])
        alpha = 0.05
        
        rate, count = calculate_empirical_error_rate(p_values, alpha)
        
        assert count == 0
        assert rate == 0.0

    def test_empirical_error_rate_all_rejections(self):
        """Test when all p-values are below alpha."""
        p_values = np.array([0.001, 0.002, 0.003, 0.004, 0.005])
        alpha = 0.05
        
        rate, count = calculate_empirical_error_rate(p_values, alpha)
        
        assert count == 5
        assert rate == 1.0

    def test_empirical_error_rate_empty_array(self):
        """Test handling of empty p-value array."""
        p_values = np.array([])
        alpha = 0.05
        
        with pytest.raises(ValueError):
            calculate_empirical_error_rate(p_values, alpha)

    def test_empirical_error_rate_with_dataframe(self):
        """Test that function works with pandas Series."""
        p_values = pd.Series([0.01, 0.04, 0.06, 0.09])
        alpha = 0.05
        
        rate, count = calculate_empirical_error_rate(p_values, alpha)
        
        assert count == 2
        assert abs(rate - 0.5) < 1e-9


class TestConfidenceInterval:
    """Contract tests for confidence interval calculation."""

    def test_ci_normal_approximation(self):
        """Test CI calculation using normal approximation."""
        n = 1000
        successes = 50
        alpha_level = 0.05  # 95% CI
        
        ci_lower, ci_upper = calculate_confidence_interval(successes, n, alpha_level)
        
        # Expected proportion
        p_hat = successes / n
        # Standard error for normal approximation
        se = np.sqrt(p_hat * (1 - p_hat) / n)
        z_critical = 1.96  # for 95% CI
        
        expected_lower = p_hat - z_critical * se
        expected_upper = p_hat + z_critical * se
        
        assert abs(ci_lower - expected_lower) < 1e-6
        assert abs(ci_upper - expected_upper) < 1e-6
        assert ci_lower < p_hat < ci_upper

    def test_ci_small_sample(self):
        """Test CI with small sample size."""
        n = 20
        successes = 5
        alpha_level = 0.05
        
        ci_lower, ci_upper = calculate_confidence_interval(successes, n, alpha_level)
        
        assert 0 <= ci_lower < ci_upper <= 1
        assert ci_lower <= (successes / n) <= ci_upper

    def test_ci_zero_successes(self):
        """Test CI when there are zero successes."""
        n = 100
        successes = 0
        alpha_level = 0.05
        
        ci_lower, ci_upper = calculate_confidence_interval(successes, n, alpha_level)
        
        assert ci_lower == 0.0
        assert ci_upper > 0.0

    def test_ci_all_successes(self):
        """Test CI when all trials are successes."""
        n = 100
        successes = 100
        alpha_level = 0.05
        
        ci_lower, ci_upper = calculate_confidence_interval(successes, n, alpha_level)
        
        assert ci_lower < 1.0
        assert ci_upper == 1.0

    def test_ci_invalid_inputs(self):
        """Test that invalid inputs raise errors."""
        # Successes > n
        with pytest.raises(ValueError):
            calculate_confidence_interval(101, 100, 0.05)
        
        # Negative successes
        with pytest.raises(ValueError):
            calculate_confidence_interval(-1, 100, 0.05)
        
        # Zero sample size
        with pytest.raises(ValueError):
            calculate_confidence_interval(0, 0, 0.05)

    def test_ci_different_confidence_levels(self):
        """Test CI calculation with different confidence levels."""
        n = 500
        successes = 25
        
        # 90% CI
        ci_90 = calculate_confidence_interval(successes, n, 0.10)
        # 95% CI
        ci_95 = calculate_confidence_interval(successes, n, 0.05)
        # 99% CI
        ci_99 = calculate_confidence_interval(successes, n, 0.01)
        
        # Higher confidence level should yield wider interval
        width_90 = ci_90[1] - ci_90[0]
        width_95 = ci_95[1] - ci_95[0]
        width_99 = ci_99[1] - ci_99[0]
        
        assert width_90 < width_95 < width_99