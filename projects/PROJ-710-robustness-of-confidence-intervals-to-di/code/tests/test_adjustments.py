"""
Unit tests for bias-correction and variance-inflation adjustments.
Tests verify the mathematical correctness of the implementation against
known theoretical properties and edge cases.
"""
import numpy as np
import pytest
import json
import os
from pathlib import Path
from code.analysis.adjustments import (
    apply_bias_correction_mean,
    apply_variance_inflation_regression,
    apply_adjustments_to_summary,
    compute_adjusted_ci
)

# Fixtures
@pytest.fixture
def simple_mean_data():
    """Generate data with known mean and variance."""
    np.random.seed(42)
    n = 1000
    true_mean = 5.0
    true_var = 4.0
    data = np.random.normal(loc=true_mean, scale=np.sqrt(true_var), size=n)
    return {
        'data': data,
        'true_mean': true_mean,
        'true_var': true_var,
        'n': n
    }

@pytest.fixture
def simple_regression_data():
    """Generate data for simple linear regression: y = 2x + noise."""
    np.random.seed(123)
    n = 500
    x = np.random.normal(0, 1, n)
    true_beta_0 = 1.0
    true_beta_1 = 2.0
    noise_std = 0.5
    y = true_beta_0 + true_beta_1 * x + np.random.normal(0, noise_std, n)
    return {
        'X': x,
        'y': y,
        'true_beta_0': true_beta_0,
        'true_beta_1': true_beta_1,
        'noise_std': noise_std,
        'n': n
    }

class TestBiasCorrectionMean:
    """Tests for apply_bias_correction_mean."""

    def test_bias_correction_identity(self, simple_mean_data):
        """
        Test that bias correction returns the original estimate when
        the DP noise scale is zero (epsilon -> infinity).
        """
        data = simple_mean_data['data']
        point_estimate = np.mean(data)
        epsilon = float('inf')  # No noise
        sensitivity = np.std(data) / np.sqrt(len(data))  # Simplified sensitivity

        corrected_mean, corrected_se = apply_bias_correction_mean(
            point_estimate, sensitivity, epsilon
        )

        # With infinite epsilon, correction should be negligible
        assert np.isclose(corrected_mean, point_estimate, rtol=1e-5)
        assert np.isclose(corrected_se, sensitivity, rtol=1e-5)

    def test_bias_correction_direction(self, simple_mean_data):
        """
        Test that bias correction moves the estimate in the expected direction
        when noise is added. Specifically, if we add positive bias, correction
        should subtract it.
        """
        data = simple_mean_data['data']
        true_mean = simple_mean_data['true_mean']
        n = simple_mean_data['n']
        
        # Simulate a scenario where we have a known bias
        # We will use a small epsilon to force a noticeable correction
        epsilon = 1.0
        sensitivity = np.std(data) / np.sqrt(n)
        
        # Introduce a known bias (simulating the effect of DP noise on the mean)
        observed_mean = true_mean + 0.5  # Artificially biased
        
        corrected_mean, _ = apply_bias_correction_mean(
            observed_mean, sensitivity, epsilon
        )
        
        # The corrected mean should be closer to the true mean than the observed
        # Note: This is a heuristic test; exact bias depends on the specific
        # noise distribution and epsilon.
        assert corrected_mean < observed_mean  # Correction should reduce the positive bias

    def test_edge_case_small_epsilon(self, simple_mean_data):
        """Test behavior when epsilon is very small (high noise)."""
        data = simple_mean_data['data']
        point_estimate = np.mean(data)
        epsilon = 1e-6
        sensitivity = np.std(data) / np.sqrt(len(data))
        
        # Should not raise an error, even with tiny epsilon
        corrected_mean, corrected_se = apply_bias_correction_mean(
            point_estimate, sensitivity, epsilon
        )
        
        # With tiny epsilon, the correction might be large, but it should be finite
        assert np.isfinite(corrected_mean)
        assert np.isfinite(corrected_se)

class TestVarianceInflationRegression:
    """Tests for apply_variance_inflation_regression."""

    def test_variance_inflation_factor(self, simple_regression_data):
        """
        Test that variance inflation is applied correctly.
        The inflated variance should be larger than the original variance.
        """
        X = simple_regression_data['X']
        y = simple_regression_data['y']
        n = simple_regression_data['n']
        
        # Calculate OLS estimates
        X_design = np.column_stack([np.ones(n), X])
        beta_hat = np.linalg.lstsq(X_design, y, rcond=None)[0]
        
        # Residuals
        residuals = y - X_design @ beta_hat
        sigma_sq_hat = np.sum(residuals**2) / (n - 2)
        
        # Covariance matrix of beta
        XtX_inv = np.linalg.inv(X_design.T @ X_design)
        var_beta = sigma_sq_hat * np.diag(XtX_inv)
        
        # Apply variance inflation for a given epsilon
        epsilon = 1.0
        # Sensitivity for regression coefficients depends on data scaling
        # For simplicity, use a normalized sensitivity
        sensitivity_sq = 1.0 / (n * np.var(X)) 
        
        adjusted_var, inflation_factor = apply_variance_inflation_regression(
            var_beta, sensitivity_sq, epsilon
        )
        
        # Inflation factor should be > 1
        assert inflation_factor > 1.0
        
        # Adjusted variance should be larger than original
        assert np.all(adjusted_var > var_beta)

    def test_variance_inflation_consistency(self, simple_regression_data):
        """
        Test that variance inflation is consistent across different epsilon values.
        """
        X = simple_regression_data['X']
        y = simple_regression_data['y']
        n = simple_regression_data['n']
        
        X_design = np.column_stack([np.ones(n), X])
        beta_hat = np.linalg.lstsq(X_design, y, rcond=None)[0]
        
        residuals = y - X_design @ beta_hat
        sigma_sq_hat = np.sum(residuals**2) / (n - 2)
        XtX_inv = np.linalg.inv(X_design.T @ X_design)
        var_beta = sigma_sq_hat * np.diag(XtX_inv)
        
        sensitivity_sq = 1.0 / (n * np.var(X))
        
        # Test with multiple epsilon values
        epsilons = [0.5, 1.0, 2.0, 5.0]
        inflation_factors = []
        
        for eps in epsilons:
            _, inf_factor = apply_variance_inflation_regression(
                var_beta, sensitivity_sq, eps
            )
            inflation_factors.append(inf_factor)
        
        # As epsilon increases, inflation factor should decrease
        for i in range(len(epsilons) - 1):
            assert inflation_factors[i] > inflation_factors[i+1], \
                f"Inflation factor should decrease as epsilon increases: {inflation_factors}"

class TestAdjustmentsToSummary:
    """Tests for apply_adjustments_to_summary."""

    def test_adjustments_to_summary_structure(self, simple_mean_data):
        """Test that the summary dictionary is correctly updated."""
        data = simple_mean_data['data']
        point_estimate = np.mean(data)
        se = np.std(data) / np.sqrt(len(data))
        
        summary = {
            'point_estimate': point_estimate,
            'standard_error': se,
            'statistic_type': 'mean',
            'epsilon': 1.0,
            'noise_type': 'laplace'
        }
        
        sensitivity = se  # Simplified sensitivity for mean
        
        adjusted_summary = apply_adjustments_to_summary(summary, sensitivity)
        
        # Check that new keys are added
        assert 'adjusted_point_estimate' in adjusted_summary
        assert 'adjusted_standard_error' in adjusted_summary
        assert 'adjustment_method' in adjusted_summary

    def test_adjustments_to_summary_regression(self, simple_regression_data):
        """Test adjustments for regression coefficients."""
        X = simple_regression_data['X']
        y = simple_regression_data['y']
        n = simple_regression_data['n']
        
        X_design = np.column_stack([np.ones(n), X])
        beta_hat = np.linalg.lstsq(X_design, y, rcond=None)[0]
        
        residuals = y - X_design @ beta_hat
        sigma_sq_hat = np.sum(residuals**2) / (n - 2)
        XtX_inv = np.linalg.inv(X_design.T @ X_design)
        var_beta = sigma_sq_hat * np.diag(XtX_inv)
        
        summary = {
            'point_estimate': beta_hat,
            'standard_error': np.sqrt(var_beta),
            'statistic_type': 'regression',
            'epsilon': 1.0,
            'noise_type': 'gaussian'
        }
        
        sensitivity_sq = 1.0 / (n * np.var(X))
        
        adjusted_summary = apply_adjustments_to_summary(summary, sensitivity_sq)
        
        assert 'adjusted_point_estimate' in adjusted_summary
        assert 'adjusted_standard_error' in adjusted_summary
        assert 'adjustment_method' in adjusted_summary

class TestAdjustedCI:
    """Tests for compute_adjusted_ci."""

    def test_adjusted_ci_width(self, simple_mean_data):
        """Test that adjusted CI is wider than unadjusted CI when noise is present."""
        data = simple_mean_data['data']
        point_estimate = np.mean(data)
        se = np.std(data) / np.sqrt(len(data))
        epsilon = 1.0
        
        # Unadjusted CI (95%)
        z = 1.96
        unadjusted_lower = point_estimate - z * se
        unadjusted_upper = point_estimate + z * se
        unadjusted_width = unadjusted_upper - unadjusted_lower
        
        sensitivity = se
        
        # Adjusted CI
        adj_lower, adj_upper = compute_adjusted_ci(
            point_estimate, se, sensitivity, epsilon, alpha=0.05
        )
        adjusted_width = adj_upper - adj_lower
        
        # Adjusted CI should be wider due to uncertainty from DP noise
        assert adjusted_width > unadjusted_width

    def test_adjusted_ci_coverage_property(self, simple_mean_data):
        """
        Test that the adjusted CI maintains coverage properties.
        This is a simplified test; full coverage validation requires simulation.
        """
        data = simple_mean_data['data']
        true_mean = simple_mean_data['true_mean']
        
        point_estimate = np.mean(data)
        se = np.std(data) / np.sqrt(len(data))
        epsilon = 2.0  # Moderate privacy budget
        
        sensitivity = se
        
        adj_lower, adj_upper = compute_adjusted_ci(
            point_estimate, se, sensitivity, epsilon, alpha=0.05
        )
        
        # Check that the CI is well-formed
        assert adj_lower < point_estimate < adj_upper
        
        # In a full test suite, we would simulate many datasets and check
        # that the true mean falls within the CI at the nominal rate (e.g., 95%)