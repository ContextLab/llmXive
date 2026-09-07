import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from analysis.tradeoff_model import logistic_function, fit_tradeoff_curve


def test_logistic_function():
    """Test the logistic function with known parameters."""
    x = np.array([0, 10, 20, 30, 40, 50])
    L, k, x0 = 1.0, 0.1, 25.0

    result = logistic_function(x, L, k, x0)

    # Check bounds
    assert all(0 <= r <= 1 for r in result)

    # Check midpoint
    mid_idx = np.argmin(np.abs(x - x0))
    assert abs(result[mid_idx] - 0.5) < 0.1

    print("Logistic function test passed.")


def test_fit_tradeoff_curve():
    """Test curve fitting with synthetic data."""
    # Create synthetic logs
    logs = []
    for pct in [10, 20, 30, 40, 50]:
        for _ in range(5):
            logs.append({
                "context_reduction_pct": pct,
                "policy_violations": [f"violation_{i}" for i in range(np.random.randint(0, 2))],
                "depth": 5,
            })

    reduction_pcts, error_rates, fitted = fit_tradeoff_curve(logs)

    assert len(reduction_pcts) == len(error_rates)
    assert len(error_rates) == len(fitted)

    print("Curve fitting test passed.")


if __name__ == "__main__":
    test_logistic_function()
    test_fit_tradeoff_curve()
