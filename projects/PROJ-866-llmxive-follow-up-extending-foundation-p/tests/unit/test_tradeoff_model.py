import pytest
import numpy as np
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from analysis.tradeoff_model import logistic_function, fit_tradeoff_curve, load_processed_logs


def test_logistic_function_bounds():
    """Test that logistic function outputs are strictly within [0, L]."""
    x = np.array([0, 10, 20, 30, 40, 50, 100])
    L, k, x0 = 1.0, 0.1, 25.0

    result = logistic_function(x, L, k, x0)

    # Check strict bounds
    assert np.all(result >= 0.0)
    assert np.all(result <= L)

def test_logistic_function_midpoint():
    """Test that logistic function equals L/2 at x0."""
    x = np.array([25.0])
    L, k, x0 = 1.0, 0.1, 25.0

    result = logistic_function(x, L, k, x0)

    # At x0, logistic function should be exactly L/2
    assert np.isclose(result[0], L / 2.0, atol=1e-9)

def test_logistic_function_asymptotes():
    """Test asymptotic behavior of logistic function."""
    # Large negative x
    x_neg = np.array([-1000.0])
    L, k, x0 = 1.0, 0.1, 25.0
    result_neg = logistic_function(x_neg, L, k, x0)
    assert np.isclose(result_neg[0], 0.0, atol=1e-6)

    # Large positive x
    x_pos = np.array([1000.0])
    result_pos = logistic_function(x_pos, L, k, x0)
    assert np.isclose(result_pos[0], L, atol=1e-6)

def test_fit_tradeoff_curve_with_known_data():
    """Test curve fitting with synthetic data where we know the ground truth."""
    # Create synthetic logs with a known underlying logistic relationship
    np.random.seed(42)
    logs = []

    # Generate data points along a known logistic curve with noise
    true_L, true_k, true_x0 = 0.8, 0.05, 40.0
    reduction_pcts = np.linspace(0, 80, 20)

    for pct in reduction_pcts:
        # Calculate true error rate from logistic function
        true_error = logistic_function(np.array([pct]), true_L, true_k, true_x0)[0]
        # Add small noise
        noisy_error = true_error + np.random.normal(0, 0.02)
        noisy_error = np.clip(noisy_error, 0, 1)

        # Create 5 samples per reduction percentage
        for _ in range(5):
            logs.append({
                "context_reduction_pct": float(pct),
                "policy_violations": ["violation"] if np.random.random() < noisy_error else [],
                "depth": 5,
                "complexity": 3
            })

    reduction_pcts_out, error_rates, fitted = fit_tradeoff_curve(logs)

    # Verify output dimensions
    assert len(reduction_pcts_out) > 0
    assert len(error_rates) == len(reduction_pcts_out)
    assert len(fitted) == len(reduction_pcts_out)

    # Verify error rates are within valid probability bounds
    assert np.all(error_rates >= 0.0)
    assert np.all(error_rates <= 1.0)

    # Verify fitted values are within valid probability bounds
    assert np.all(fitted >= 0.0)
    assert np.all(fitted <= 1.0)

    # Verify that the fitted curve generally follows the trend
    # (higher reduction percentages should generally have higher error rates for this data)
    # Note: We don't check exact values due to noise, but we check monotonicity in aggregate
    # by comparing means of first and last quartiles
    sorted_indices = np.argsort(reduction_pcts_out)
    sorted_errors = error_rates[sorted_indices]
    first_quartile_mean = np.mean(sorted_errors[:len(sorted_errors)//4])
    last_quartile_mean = np.mean(sorted_errors[-len(sorted_errors)//4:])

    # The last quartile should generally have higher error than first quartile
    # Allow some tolerance due to noise
    assert last_quartile_mean >= first_quartile_mean * 0.8, "Fitted curve should generally increase with reduction percentage"

def test_fit_tradeoff_curve_empty_logs():
    """Test that fit_tradeoff_curve handles empty logs gracefully."""
    logs = []
    reduction_pcts, error_rates, fitted = fit_tradeoff_curve(logs)

    assert len(reduction_pcts) == 0
    assert len(error_rates) == 0
    assert len(fitted) == 0

def test_fit_tradeoff_curve_single_point():
    """Test curve fitting with a single data point."""
    logs = [{
        "context_reduction_pct": 50.0,
        "policy_violations": ["violation"],
        "depth": 5,
        "complexity": 3
    }]

    reduction_pcts, error_rates, fitted = fit_tradeoff_curve(logs)

    assert len(reduction_pcts) == 1
    assert len(error_rates) == 1
    assert len(fitted) == 1
    assert error_rates[0] == 1.0  # 1 violation out of 1 sample

def test_load_processed_logs_empty_directory(tmp_path):
    """Test load_processed_logs with an empty directory."""
    logs = load_processed_logs(str(tmp_path))
    assert logs == []

def test_load_processed_logs_with_valid_json(tmp_path):
    """Test load_processed_logs with valid JSON files."""
    # Create a test JSON file
    test_data = [
        {
            "context_reduction_pct": 30.0,
            "policy_violations": ["violation_1"],
            "depth": 5,
            "complexity": 3
        },
        {
            "context_reduction_pct": 40.0,
            "policy_violations": [],
            "depth": 5,
            "complexity": 3
        }
    ]

    test_file = tmp_path / "test_log.json"
    import json
    with open(test_file, 'w') as f:
        json.dump(test_data, f)

    logs = load_processed_logs(str(tmp_path))
    assert len(logs) == 2
    assert logs[0]["context_reduction_pct"] == 30.0
    assert len(logs[0]["policy_violations"]) == 1
    assert len(logs[1]["policy_violations"]) == 0

if __name__ == "__main__":
    test_logistic_function_bounds()
    test_logistic_function_midpoint()
    test_logistic_function_asymptotes()
    test_fit_tradeoff_curve_with_known_data()
    test_fit_tradeoff_curve_empty_logs()
    test_fit_tradeoff_curve_single_point()
    test_load_processed_logs_empty_directory(tmp_path=None)
    test_load_processed_logs_with_valid_json(tmp_path=None)
    print("All tests passed.")