"""
Unit tests for regression analysis functionality in code/regression_analysis.py.
Verifies exponent, confidence interval, and p-value calculations.
"""

import pytest
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import OLSInfluence
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from regression_analysis import run_ols_regression, analyze_scaling_law


class TestRegressionOutputs:
    """Tests for regression analysis outputs: exponent, CI, and p-value."""

    def test_run_ols_regression_returns_expected_keys(self):
        """Test that run_ols_regression returns a dictionary with required keys."""
        # Generate synthetic but realistic data for testing
        np.random.seed(42)
        n_samples = 50
        x = np.random.uniform(2.0, 6.0, n_samples)  # average degree
        y = 2.5 * np.log(x) + np.random.normal(0, 0.1, n_samples)  # log conductivity

        # Run regression
        result = run_ols_regression(x, y)

        # Check required keys exist
        assert isinstance(result, dict)
        assert 'exponent' in result
        assert 'confidence_interval' in result
        assert 'p_value' in result
        assert 'r_squared' in result
        assert 'model' in result

    def test_run_ols_regression_exponent_accuracy(self):
        """Test that exponent is calculated correctly for known relationship."""
        np.random.seed(123)
        n_samples = 100
        x = np.linspace(2.0, 8.0, n_samples)
        true_exponent = 1.5
        # y = exponent * log(x) + noise
        y = true_exponent * np.log(x) + np.random.normal(0, 0.05, n_samples)

        result = run_ols_regression(x, y)

        # The exponent should be close to the true value (within 10%)
        assert abs(result['exponent'] - true_exponent) < 0.15

    def test_run_ols_regression_confidence_interval_validity(self):
        """Test that confidence interval is a valid 2-tuple and contains exponent."""
        np.random.seed(456)
        n_samples = 80
        x = np.random.uniform(2.0, 6.0, n_samples)
        y = 2.0 * np.log(x) + np.random.normal(0, 0.1, n_samples)

        result = run_ols_regression(x, y)

        ci = result['confidence_interval']
        assert isinstance(ci, tuple)
        assert len(ci) == 2
        assert ci[0] <= result['exponent'] <= ci[1]
        assert ci[0] > 0  # Exponents should be positive in this context
        assert ci[1] > 0

    def test_run_ols_regression_p_value_range(self):
        """Test that p-value is in valid range [0, 1]."""
        np.random.seed(789)
        n_samples = 60
        x = np.random.uniform(2.0, 6.0, n_samples)
        y = 1.8 * np.log(x) + np.random.normal(0, 0.15, n_samples)

        result = run_ols_regression(x, y)

        p_value = result['p_value']
        assert 0.0 <= p_value <= 1.0

    def test_run_ols_regression_with_perfect_correlation(self):
        """Test regression with nearly perfect correlation (noise=0)."""
        np.random.seed(999)
        n_samples = 30
        x = np.linspace(2.0, 6.0, n_samples)
        true_exponent = 3.0
        y = true_exponent * np.log(x)  # No noise

        result = run_ols_regression(x, y)

        # With perfect data, exponent should match exactly (within floating point)
        assert abs(result['exponent'] - true_exponent) < 1e-6
        # R-squared should be very close to 1
        assert result['r_squared'] > 0.999
        # P-value should be very small
        assert result['p_value'] < 0.001

    def test_run_ols_regression_with_high_noise(self):
        """Test regression with high noise (should still produce valid outputs)."""
        np.random.seed(111)
        n_samples = 100
        x = np.random.uniform(2.0, 6.0, n_samples)
        true_exponent = 2.0
        y = true_exponent * np.log(x) + np.random.normal(0, 1.0, n_samples)  # High noise

        result = run_ols_regression(x, y)

        # Should still produce valid structure
        assert isinstance(result['exponent'], (int, float))
        assert isinstance(result['confidence_interval'], tuple)
        assert len(result['confidence_interval']) == 2
        assert isinstance(result['p_value'], (int, float))
        assert 0.0 <= result['p_value'] <= 1.0

    def test_analyze_scaling_law_integration(self):
        """Test the full analyze_scaling_law function which wraps regression."""
        # Create a mock DataFrame with simulation results
        np.random.seed(222)
        n_samples = 50
        df_data = {
            'avg_degree': np.random.uniform(2.5, 7.5, n_samples),
            'conductivity': np.random.uniform(10, 500, n_samples),
            'percolation_flag': np.random.choice([0, 1], n_samples)
        }
        df = pd.DataFrame(df_data)

        # Filter for percolated networks
        percolated_df = df[df['percolation_flag'] == 1]

        if len(percolated_df) > 10:  # Need enough samples
            result = analyze_scaling_law(percolated_df)

            # Verify result structure
            assert 'scaling_exponent' in result
            assert 'confidence_interval' in result
            assert 'p_value' in result
            assert 'r_squared' in result
            assert 'significant' in result

            # Verify types
            assert isinstance(result['scaling_exponent'], float)
            assert isinstance(result['confidence_interval'], tuple)
            assert isinstance(result['p_value'], float)
            assert isinstance(result['significant'], bool)

    def test_regression_with_small_sample(self):
        """Test regression with minimal sample size (edge case)."""
        np.random.seed(333)
        x = np.array([2.0, 3.0, 4.0, 5.0, 6.0])
        y = np.array([1.0, 1.5, 2.0, 2.5, 3.0])

        result = run_ols_regression(x, y)

        # Should handle small samples gracefully
        assert 'exponent' in result
        assert 'p_value' in result
        assert 0.0 <= result['p_value'] <= 1.0

    def test_regression_handles_log_transformation(self):
        """Verify that regression operates on log-transformed data as expected."""
        np.random.seed(444)
        n_samples = 40
        x = np.random.uniform(2.0, 6.0, n_samples)
        true_exponent = 2.2
        # Data follows power law: conductivity = k * (avg_degree)^exponent
        # Log-transformed: log(conductivity) = log(k) + exponent * log(avg_degree)
        y_log = true_exponent * np.log(x) + np.random.normal(0, 0.1, n_samples)

        result = run_ols_regression(x, y_log)

        # The exponent should match the true exponent from the log-transformed relationship
        assert abs(result['exponent'] - true_exponent) < 0.15

    def test_regression_outputs_match_statsmodels_format(self):
        """Test that regression outputs are consistent with statsmodels OLSInfluence."""
        np.random.seed(555)
        n_samples = 60
        x = np.random.uniform(2.0, 6.0, n_samples)
        y = 1.9 * np.log(x) + np.random.normal(0, 0.1, n_samples)

        # Run our regression
        result = run_ols_regression(x, y)

        # Manually verify using statsmodels directly
        X = sm.add_constant(x)
        model = sm.OLS(y, X).fit()

        # Compare key statistics
        assert abs(result['exponent'] - model.params[1]) < 1e-10
        assert abs(result['r_squared'] - model.rsquared) < 1e-10

        # P-value for the slope coefficient
        p_value_manual = model.pvalues[1]
        assert abs(result['p_value'] - p_value_manual) < 1e-10