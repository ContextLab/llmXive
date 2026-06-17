"""Tests for the regression analysis module."""

import pandas as pd
import pytest

from analysis.regression import run_regression_analysis, compute_correlation_metrics, compute_vif


@pytest.fixture
def sample_data():
    # Create a tiny synthetic dataset with a clear relationship
    data = {
        "crossing_number": [3, 4, 5, 6, 7],
        "braid_index": [2, 2, 3, 3, 4],
        "hyperbolic_volume": [1.2, 1.5, 2.0, 2.4, 3.1],
    }
    return pd.DataFrame(data)


def test_compute_correlation_metrics(sample_data):
    metrics = compute_correlation_metrics(
        df=sample_data,
        target="hyperbolic_volume",
        predictors=["crossing_number", "braid_index"],
    )
    assert set(metrics.keys()) == {"crossing_number", "braid_index"}
    for vals in metrics.values():
        assert "pearson" in vals and "spearman" in vals
        # Correlations should be positive for this synthetic data
        assert vals["pearson"] > 0
        assert vals["spearman"] > 0


def test_compute_vif(sample_data):
    vif = compute_vif(sample_data, ["crossing_number", "braid_index"])
    assert set(vif.keys()) == {"crossing_number", "braid_index"}
    # VIF values should be finite and >= 1
    for val in vif.values():
        assert val >= 1.0
        assert val != float("inf")


def test_run_regression_analysis(sample_data):
    report = run_regression_analysis(
        df=sample_data,
        target="hyperbolic_volume",
        predictors=["crossing_number", "braid_index"],
    )
    # Expect three model reports
    assert set(report.keys()) == {"linear", "polynomial", "logarithmic"}
    for model_name, metrics in report.items():
        # Each model should report the required metrics
        for key in ["r_squared", "aic", "bic", "mae", "rmse"]:
            assert key in metrics
            # Basic sanity check: values should be numeric
            assert isinstance(metrics[key], float)