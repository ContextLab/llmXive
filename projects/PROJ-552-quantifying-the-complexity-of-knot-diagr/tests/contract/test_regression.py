"""Contract test for regression model output.

This test verifies that the regression analysis module produces a
deterministic output schema given a well‑formed input DataFrame.
It does not depend on any external data files; a synthetic dataset
is constructed in‑memory.

Expected contract:
  - The ``run_regression_analysis`` function returns a mapping
    (dict) with entries for each model type: ``linear``,
    ``polynomial``, and ``logarithmic``.
  - Each model entry contains the core goodness‑of‑fit metrics:
    ``r_squared``, ``aic``, ``bic``, ``mae``, and ``rmse``.
"""

import pandas as pd
import pytest

# The analysis module provides a high‑level helper that fits the
# three regression models and returns a report dictionary.
from analysis.regression import run_regression_analysis

@pytest.fixture
def synthetic_knots_df():
    """Create a minimal synthetic dataset for regression testing."""
    # The dataset includes the two core invariants (crossing number,
    # braid index) and a continuous target (hyperbolic volume) that
    # exhibits a monotonic relationship with the predictors.
    data = {
        "crossing_number": [3, 4, 5, 6, 7, 8, 9],
        "braid_index":    [2, 2, 3, 3, 4, 4, 5],
        "hyperbolic_volume": [1.1, 2.0, 3.2, 4.1, 5.3, 6.2, 7.5],
    }
    return pd.DataFrame(data)

def test_regression_output_schema(synthetic_knots_df):
    """Validate that the regression report conforms to the contract."""
    # Run the regression analysis on the synthetic data.
    report = run_regression_analysis(
        df=synthetic_knots_df,
        target="hyperbolic_volume",
        predictors=["crossing_number", "braid_index"],
    )

    # The contract requires a dictionary with three model entries.
    assert isinstance(report, dict), "Report should be a dict"
    expected_models = {"linear", "polynomial", "logarithmic"}
    assert set(report.keys()) == expected_models, (
        f"Report keys {report.keys()} do not match expected {expected_models}"
    )

    # Each model entry must contain the core goodness‑of‑fit metrics.
    required_metrics = {"r_squared", "aic", "bic", "mae", "rmse"}
    for model_name, metrics in report.items():
        assert isinstance(metrics, dict), f"Metrics for {model_name} should be a dict"
        missing = required_metrics - set(metrics.keys())
        assert not missing, f"Model {model_name} missing metrics: {missing}"
        
        # Basic type checks – all metrics are numeric (int or float).
        for metric_name in required_metrics:
            value = metrics[metric_name]
            assert isinstance(value, (int, float)), (
                f"Metric {metric_name} for model {model_name} must be numeric"
            )
        
        # Logical sanity checks (e.g., R² between 0 and 1 for these synthetic data).
        r2 = metrics["r_squared"]
        assert 0.0 <= r2 <= 1.0, f"R² for {model_name} out of bounds: {r2}"