"""
Unit tests for sensitivity analysis functionality (FR-007).
"""
import pytest
import pandas as pd
import numpy as np
from analysis.sensitivity import analyze_thresholds, run_sensitivity_sweep


@pytest.fixture
def synthetic_data():
    """Create synthetic aligned data with known correlation."""
    np.random.seed(42)
    n = 1000
    # Create Vsw with varying speeds
    vsw = np.random.uniform(300, 800, n)
    # Create Ey with linear relationship to Vsw + noise
    ey = 0.5 * vsw + np.random.normal(0, 10, n)
    return pd.Series(vsw), pd.Series(ey)


def test_analyze_thresholds_basic(synthetic_data):
    """Test basic threshold analysis returns expected structure."""
    vsw, ey = synthetic_data
    results = analyze_thresholds(vsw, ey)

    assert "low" in results
    assert "medium" in results
    assert "high" in results

    # Check structure of each result
    for label, res in results.items():
        assert "threshold" in res
        assert "count" in res
        assert "correlation" in res
        assert "p_value" in res
        assert res["count"] > 0
        assert not np.isnan(res["correlation"])


def test_analyze_thresholds_custom_thresholds(synthetic_data):
    """Test with custom threshold values."""
    vsw, ey = synthetic_data
    custom_thresholds = {"very_low": 350.0, "very_high": 700.0}
    results = analyze_thresholds(vsw, ey, thresholds=custom_thresholds)

    assert "very_low" in results
    assert "very_high" in results
    assert "low" not in results  # Default should not be present

    # Very high threshold should have fewer samples
    assert results["very_high"]["count"] < results["very_low"]["count"]


def test_analyze_thresholds_with_lag(synthetic_data):
    """Test threshold analysis with lag shift applied."""
    vsw, ey = synthetic_data
    results_no_lag = analyze_thresholds(vsw, ey, lag_minutes=0)
    results_with_lag = analyze_thresholds(vsw, ey, lag_minutes=10)

    # Results should differ due to lag
    assert results_no_lag["medium"]["correlation"] != results_with_lag["medium"]["correlation"]


def test_analyze_thresholds_insufficient_data():
    """Test handling of insufficient data at high threshold."""
    # Create small dataset
    vsw = pd.Series([300.0, 350.0, 400.0])
    ey = pd.Series([10.0, 15.0, 20.0])

    # Set threshold higher than any value
    results = analyze_thresholds(vsw, ey, thresholds={"high": 500.0})

    assert results["high"]["count"] == 0
    assert np.isnan(results["high"]["correlation"])
    assert "note" in results["high"]


def test_run_sensitivity_sweep(synthetic_data):
    """Test full sensitivity sweep across multiple lags."""
    vsw, ey = synthetic_data
    sweep_results = run_sensitivity_sweep(vsw, ey, lag_candidates=[0, 5, 10])

    assert "lag_0" in sweep_results
    assert "lag_5" in sweep_results
    assert "lag_10" in sweep_results

    # Each lag result should contain threshold analyses
    for lag_key, threshold_results in sweep_results.items():
        assert "medium" in threshold_results
        assert "correlation" in threshold_results["medium"]


def test_threshold_filtering_logic(synthetic_data):
    """Verify that filtering actually reduces dataset size."""
    vsw, ey = synthetic_data

    results = analyze_thresholds(vsw, ey)

    # Higher thresholds should have fewer or equal samples
    assert results["high"]["count"] <= results["medium"]["count"]
    assert results["medium"]["count"] <= results["low"]["count"]

    # All counts should be positive (for this synthetic data)
    assert results["low"]["count"] > 0
    assert results["medium"]["count"] > 0
    assert results["high"]["count"] > 0