"""
Tests for the metrics module.
"""
import pytest
import numpy as np
import pandas as pd

from code.analysis.metrics import calculate_bias_metrics
from code.analysis.entities import CausalEstimate


def test_calculate_bias_metrics_list():
    """Test calculate_bias_metrics with a list of CausalEstimate objects."""
    # Create ground truth
    ground_truth = 0.5

    # Create estimates with known errors
    # Estimate 1: 0.5 (error 0)
    # Estimate 2: 0.6 (error 0.1)
    # Estimate 3: 0.4 (error -0.1)
    estimates = [
        CausalEstimate(method="Mean", estimator="IPW", ate=0.5, se=0.05, ci_lower=0.4, ci_upper=0.6),
        CausalEstimate(method="Mean", estimator="PSM", ate=0.6, se=0.05, ci_lower=0.5, ci_upper=0.7),
        CausalEstimate(method="KNN", estimator="IPW", ate=0.4, se=0.05, ci_lower=0.3, ci_upper=0.5),
    ]

    result = calculate_bias_metrics(estimates, ground_truth)

    # Expected calculations:
    # Errors: [0, 0.1, -0.1]
    # Absolute Errors: [0, 0.1, 0.1] -> Mean = 0.0666...
    # Squared Errors: [0, 0.01, 0.01] -> Mean = 0.00666... -> Sqrt = 0.0816...
    
    expected_abs_bias = np.mean([0, 0.1, 0.1])
    expected_rmse = np.sqrt(np.mean([0**2, 0.1**2, (-0.1)**2]))

    assert abs(result['absolute_bias'] - expected_abs_bias) < 1e-6
    assert abs(result['rmse'] - expected_rmse) < 1e-6
    assert result['count'] == 3
    assert abs(result['mean_estimate'] - 0.5) < 1e-6


def test_calculate_bias_metrics_dataframe():
    """Test calculate_bias_metrics with a DataFrame."""
    ground_truth = 10.0
    
    df = pd.DataFrame({
        'method': ['A', 'B', 'C'],
        'ate': [11.0, 9.0, 10.0]
    })

    result = calculate_bias_metrics(df, ground_truth)

    # Errors: [1, -1, 0]
    # Abs Errors: [1, 1, 0] -> Mean = 0.666...
    # Sq Errors: [1, 1, 0] -> Mean = 0.666... -> Sqrt = 0.816...

    expected_abs_bias = np.mean([1, 1, 0])
    expected_rmse = np.sqrt(np.mean([1**2, (-1)**2, 0**2]))

    assert abs(result['absolute_bias'] - expected_abs_bias) < 1e-6
    assert abs(result['rmse'] - expected_rmse) < 1e-6


def test_calculate_bias_metrics_empty_list():
    """Test that an empty list raises ValueError."""
    with pytest.raises(ValueError, match="Estimates list cannot be empty"):
        calculate_bias_metrics([], 0.5)


def test_calculate_bias_metrics_invalid_ground_truth():
    """Test that invalid ground truth raises ValueError."""
    with pytest.raises(ValueError, match="ground_truth must be a valid numeric value"):
        calculate_bias_metrics([CausalEstimate("A", "B", 1.0, 0.1, 0.8, 1.2)], None)


def test_calculate_bias_metrics_invalid_input_type():
    """Test that invalid input type raises TypeError."""
    with pytest.raises(TypeError):
        calculate_bias_metrics("not a list", 0.5)


def test_calculate_bias_metrics_with_nan():
    """Test that NaN values in estimates are ignored."""
    ground_truth = 5.0
    estimates = [
        CausalEstimate(method="M", estimator="E", ate=5.0, se=0.1, ci_lower=4.8, ci_upper=5.2),
        CausalEstimate(method="M", estimator="E", ate=np.nan, se=0.1, ci_lower=4.8, ci_upper=5.2),
    ]
    
    result = calculate_bias_metrics(estimates, ground_truth)
    
    # Only the first estimate (5.0) should be used.
    # Error = 0.
    assert result['absolute_bias'] == 0.0
    assert result['count'] == 1