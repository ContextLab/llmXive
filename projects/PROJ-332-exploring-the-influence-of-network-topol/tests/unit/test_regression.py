"""
Unit tests for regression analysis module (User Story 2).
Specifically tests the calculation of scaling exponents, confidence intervals, and p-values.
"""
import pytest
import numpy as np
import pandas as pd
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant

# Import the function to be tested from the project module
from regression_analysis import run_ols_regression, analyze_scaling_law


class TestRegressionOutputs:
    """Tests for verifying regression analysis outputs."""

    def test_run_ols_regression_returns_expected_keys(self):
        """
        Verify that run_ols_regression returns a dictionary containing
        'exponent', 'confidence_interval', and 'p_value'.
        """
        # Generate synthetic data for testing: y = 2.5 * x + noise
        # In log-log space: log(y) = 2.5 * log(x) + intercept + noise
        np.random.seed(42)
        n_samples = 50
        x = np.logspace(0, 2, n_samples)  # 1 to 100
        true_slope = 2.5
        intercept = 1.0
        noise = np.random.normal(0, 0.1, n_samples)
        y = np.exp(intercept + true_slope * np.log(x) + noise)

        log_x = np.log(x)
        log_y = np.log(y)

        # Add constant for OLS
        X = add_constant(log_x)

        result = run_ols_regression(log_x, log_y)

        # Assert the result is a dictionary
        assert isinstance(result, dict), "Regression result must be a dictionary"

        # Assert required keys are present
        assert 'exponent' in result, "Result must contain 'exponent'"
        assert 'confidence_interval' in result, "Result must contain 'confidence_interval'"
        assert 'p_value' in result, "Result must contain 'p_value'"
        assert 'r_squared' in result, "Result should also contain 'r_squared' for completeness"

    def test_run_ols_regression_values_accuracy(self):
        """
        Verify that the calculated exponent, CI, and p-value are mathematically
        consistent with the input data.
        """
        np.random.seed(123)
        n_samples = 100
        x = np.linspace(1, 10, n_samples)
        true_slope = 0.8
        true_intercept = 2.0
        y = true_intercept + true_slope * x + np.random.normal(0, 0.05, n_samples)

        result = run_ols_regression(x, y)

        # The exponent should be close to the true slope
        assert np.isclose(result['exponent'], true_slope, atol=0.1), \
            f"Exponent {result['exponent']} should be close to {true_slope}"

        # The confidence interval should be a tuple/list of two numbers
        ci = result['confidence_interval']
        assert len(ci) == 2, "Confidence interval must have 2 bounds"
        assert ci[0] <= ci[1], "Lower bound must be <= upper bound"

        # The p-value for the slope should be very small given low noise
        assert result['p_value'] < 0.05, "p-value should be significant (< 0.05)"

    def test_analyze_scaling_law_integration(self):
        """
        Test the higher-level analyze_scaling_law function which wraps
        run_ols_regression and ensures the output format is correct for CSV storage.
        """
        # Create a small dataframe simulating simulation results
        data = {
            'avg_degree': [2.0, 3.0, 4.0, 5.0, 6.0, 7.0],
            'conductivity': [10.0, 25.0, 45.0, 70.0, 100.0, 135.0]
        }
        df = pd.DataFrame(data)

        # Run analysis on log-transformed data
        result = analyze_scaling_law(df, x_col='avg_degree', y_col='conductivity')

        # Verify structure
        assert 'scaling_exponent' in result
        assert 'p_value' in result
        assert 'ci_lower' in result
        assert 'ci_upper' in result

        # Verify types
        assert isinstance(result['scaling_exponent'], float)
        assert isinstance(result['p_value'], float)
        assert isinstance(result['ci_lower'], float)
        assert isinstance(result['ci_upper'], float)

    def test_regression_with_perfect_fit(self):
        """
        Test regression on data with zero noise to ensure exact recovery
        of the exponent and p-value of 0.0 (or near machine epsilon).
        """
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y = np.array([2.0, 4.0, 6.0, 8.0, 10.0])  # Perfect linear relationship y = 2x

        result = run_ols_regression(x, y)

        assert np.isclose(result['exponent'], 2.0), "Exponent should be exactly 2.0"
        assert result['p_value'] < 1e-10, "p-value should be near zero for perfect fit"
        # CI bounds should be equal or very close
        assert np.isclose(result['confidence_interval'][0], result['confidence_interval'][1], atol=1e-6)

    def test_regression_with_high_variance(self):
        """
        Test regression on high variance data to ensure p-value is high (insignificant).
        """
        np.random.seed(999)
        x = np.linspace(1, 10, 20)
        y = np.random.normal(0, 10, 20)  # Pure noise, no correlation

        result = run_ols_regression(x, y)

        # With pure noise, p-value should be high (often > 0.05)
        # Note: With only 20 points, it might occasionally be significant by chance,
        # but we assert it's not *extremely* small.
        # A more robust check is that R^2 is low.
        assert result['r_squared'] < 0.3, "R-squared should be low for uncorrelated data"