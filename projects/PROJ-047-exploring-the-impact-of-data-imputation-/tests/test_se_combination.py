"""
Tests for Standard Error and Confidence Interval combination logic.
Verifies that apply_bootstrap_ci and apply_rubins_rules produce
standard errors within expected bounds for known synthetic distributions.
"""
import numpy as np
import pytest
from typing import List, Dict, Any
import sys
import os

# Add parent directory to path to allow imports from code/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from analysis.se_combination import apply_rubins_rules, apply_bootstrap_ci
from analysis.entities import CausalEstimate


class TestBootstrapCI:
    """Tests for apply_bootstrap_ci function."""

    def test_bootstrap_ci_known_normal_distribution(self):
        """
        Verify apply_bootstrap_ci produces SE within expected bounds
        for a known normal distribution.
        
        For a normal distribution N(mu, sigma^2), the standard error of the mean
        is sigma / sqrt(n). We generate data with known parameters and verify
        the calculated SE is close to the theoretical value.
        """
        # Generate known normal distribution
        np.random.seed(42)
        n_samples = 1000
        true_mean = 5.0
        true_std = 2.0
        
        # Create CausalEstimate objects representing bootstrap samples
        # In reality, these would come from resampling, but for testing
        # we simulate the distribution of estimates
        estimates = [
            CausalEstimate(
              ate=np.random.normal(true_mean, true_std / np.sqrt(100)),  # SE of mean
              se=true_std / np.sqrt(100),
              ci_lower=None,
              ci_upper=None,
              method="bootstrap",
              estimator="mean"
            )
            for _ in range(1000)
        ]
        
        # Apply bootstrap CI
        result = apply_bootstrap_ci([e.ate for e in estimates], n_boot=500)
        
        # Theoretical SE of the mean of these estimates
        theoretical_se = true_std / np.sqrt(100) / np.sqrt(1000)  # SE of the mean of 1000 samples
        
        # Check that the calculated SE is within 20% of theoretical
        # (allowing for sampling variation)
        calculated_se = result['std_error']
        assert abs(calculated_se - theoretical_se) < 0.2 * theoretical_se, \
            f"Calculated SE {calculated_se:.4f} not within bounds of theoretical {theoretical_se:.4f}"
        
        # Verify CI contains true mean (with high probability)
        assert result['ci_lower'] <= true_mean <= result['ci_upper'], \
            f"True mean {true_mean} not in CI [{result['ci_lower']}, {result['ci_upper']}]"

    def test_bootstrap_ci_zero_variance(self):
        """Test that zero variance input produces zero SE."""
        estimates = [0.0] * 100  # All estimates are the same
        
        result = apply_bootstrap_ci(estimates, n_boot=100)
        
        # SE should be very close to zero
        assert result['std_error'] < 1e-10, "SE should be near zero for constant input"

    def test_bootstrap_ci_positive_variance(self):
        """Test that positive variance input produces positive SE."""
        estimates = [float(i) for i in range(100)]  # Increasing sequence
        
        result = apply_bootstrap_ci(estimates, n_boot=100)
        
        # SE should be positive
        assert result['std_error'] > 0, "SE should be positive for varying input"


class TestRubinsRules:
    """Tests for apply_rubins_rules function."""

    def test_rubins_rules_known_normal_distribution(self):
        """
        Verify apply_rubins_rules produces SE within expected bounds
        for multiple imputations of a known normal distribution.
        
        Rubin's rules combine within-imputation and between-imputation variance.
        For m imputations with Q_i estimates and U_i variances:
        - Q_bar = mean(Q_i)
        - U_bar = mean(U_i)
        - B = variance(Q_i)
        - T = U_bar + (1 + 1/m) * B
        """
        np.random.seed(42)
        
        # Simulate 5 imputations (m=5)
        m = 5
        true_mean = 10.0
        true_var = 4.0  # Within-imputation variance
        
        # Generate imputation estimates and their SEs
        estimates_list = []
        for _ in range(m):
            # Each imputation has a slightly different estimate
            q_i = np.random.normal(true_mean, np.sqrt(true_var / 100))  # SE of estimate
            u_i = true_var / 100  # Variance of the estimate
            
            estimates_list.append(
                CausalEstimate(
                  ate=q_i,
                  se=np.sqrt(u_i),
                  ci_lower=None,
                  ci_upper=None,
                  method="mice",
                  estimator="mean"
                )
            )
        
        # Apply Rubin's rules
        result = apply_rubins_rules(estimates_list)
        
        # Theoretical combined variance using Rubin's rules
        q_bar = np.mean([e.ate for e in estimates_list])
        u_bar = np.mean([e.se**2 for e in estimates_list])
        b = np.var([e.ate for e in estimates_list], ddof=1)
        t_theoretical = u_bar + (1 + 1/m) * b
        se_theoretical = np.sqrt(t_theoretical)
        
        # Check that calculated SE is close to theoretical
        calculated_se = result['std_error']
        
        # Allow for some sampling variation in the simulation
        assert abs(calculated_se - se_theoretical) < 0.3 * se_theoretical, \
            f"Calculated SE {calculated_se:.4f} not within bounds of theoretical {se_theoretical:.4f}"
        
        # Verify CI contains true mean (with reasonable probability)
        assert result['ci_lower'] <= true_mean <= result['ci_upper'], \
            f"True mean {true_mean} not in CI [{result['ci_lower']}, {result['ci_upper']}]"

    def test_rubins_rules_single_imputation(self):
        """Test behavior with single imputation (m=1)."""
        estimates_list = [
            CausalEstimate(
              ate=5.0,
              se=1.0,
              ci_lower=None,
              ci_upper=None,
              method="mice",
              estimator="mean"
            )
        ]
        
        result = apply_rubins_rules(estimates_list)
        
        # With single imputation, SE should equal the input SE
        assert abs(result['std_error'] - 1.0) < 1e-10, \
            f"Single imputation SE {result['std_error']} should equal input SE 1.0"

    def test_rubins_rules_large_between_variance(self):
        """Test that large between-imputation variance increases total SE."""
        np.random.seed(42)
        
        # Create estimates with large between-imputation variance
        estimates_list = [
            CausalEstimate(
              ate=float(i * 10),  # Large spread
              se=1.0,
              ci_lower=None,
              ci_upper=None,
              method="mice",
              estimator="mean"
            )
            for i in range(5)
        ]
        
        result = apply_rubins_rules(estimates_list)
        
        # SE should be significantly larger than the within-imputation SE
        assert result['std_error'] > 5.0, \
            f"SE {result['std_error']} should be large due to high between-imputation variance"

    def test_rubins_rules_small_between_variance(self):
        """Test that small between-imputation variance results in SE close to within-SE."""
        np.random.seed(42)
        
        # Create estimates with small between-imputation variance
        base_se = 1.0
        estimates_list = [
            CausalEstimate(
              ate=10.0 + np.random.normal(0, 0.1),  # Small spread
              se=base_se,
              ci_lower=None,
              ci_upper=None,
              method="mice",
              estimator="mean"
            )
            for _ in range(5)
        ]
        
        result = apply_rubins_rules(estimates_list)
        
        # SE should be close to the within-imputation SE
        assert abs(result['std_error'] - base_se) < 0.5 * base_se, \
            f"SE {result['std_error']} should be close to within-SE {base_se}"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_list_bootstrap(self):
        """Test that empty list raises appropriate error for bootstrap."""
        with pytest.raises(ValueError):
            apply_bootstrap_ci([], n_boot=100)

    def test_empty_list_rubins(self):
        """Test that empty list raises appropriate error for Rubin's rules."""
        with pytest.raises(ValueError):
            apply_rubins_rules([])

    def test_single_element_bootstrap(self):
        """Test bootstrap with single element."""
        result = apply_bootstrap_ci([5.0], n_boot=100)
        
        # SE should be zero for single element
        assert result['std_error'] == 0.0

    def test_single_element_rubins(self):
        """Test Rubin's rules with single element."""
        estimates_list = [
            CausalEstimate(
              ate=5.0,
              se=1.0,
              ci_lower=None,
              ci_upper=None,
              method="mice",
              estimator="mean"
            )
        ]
        
        result = apply_rubins_rules(estimates_list)
        
        # SE should equal input SE for single imputation
        assert abs(result['std_error'] - 1.0) < 1e-10