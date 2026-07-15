"""
Unit tests for sensitivity analysis.
File: projects/PROJ-300-exploring-the-relationship-between-solar/tests/unit/test_sensitivity.py
"""
import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.analysis.sensitivity import analyze_thresholds, run_sensitivity_sweep
from code.analysis.correlation import calculate_correlation
from code.analysis.lag_search import find_optimal_lag


def generate_test_data(n_points=1000, start_date=None):
    """Generate synthetic time series for testing."""
    if start_date is None:
        start_date = datetime(2023, 1, 1)

    timestamps = pd.date_range(start=start_date, periods=n_points, freq='5min')
    # Create a simple correlated series with noise
    base_vsw = np.random.normal(500, 100, n_points)
    base_vsw = np.clip(base_vsw, 300, 800)  # Keep within realistic range

    # Ey correlates with Vsw with some lag and noise
    lag_idx = 10  # 50 minutes lag (10 * 5min)
    base_ey = np.zeros(n_points)
    for i in range(lag_idx, n_points):
        base_ey[i] = 0.5 * base_vsw[i - lag_idx] + np.random.normal(0, 0.5)

    df_vsw = pd.Series(base_vsw, index=timestamps)
    df_ey = pd.Series(base_ey, index=timestamps)

    return df_vsw, df_ey, timestamps


def test_threshold_filtering():
    """Test that thresholds correctly filter the data."""
    df_vsw, df_ey, timestamps = generate_test_data(n_points=1000)

    # High threshold should result in fewer samples
    results = analyze_thresholds(df_vsw, df_ey, timestamps, thresholds=[400.0, 600.0])

    assert "400.0" in results
    assert "600.0" in results
    assert results["400.0"]["n_samples"] > results["600.0"]["n_samples"]
    assert results["600.0"]["n_samples"] > 0


def test_sensitivity_correlation_calculation():
    """Test that correlation is calculated for each threshold."""
    df_vsw, df_ey, timestamps = generate_test_data(n_points=2000)

    results = analyze_thresholds(df_vsw, df_ey, timestamps, thresholds=[400.0, 500.0, 600.0])

    for t in ["400.0", "500.0", "600.0"]:
        assert t in results
        assert "correlation" in results[t]
        assert "optimal_lag_min" in results[t]
        assert "p_value" in results[t]
        assert "n_samples" in results[t]
        
        # Correlation should be a float
        assert isinstance(results[t]["correlation"], float)
        # Correlation should be between -1 and 1
        assert -1.0 <= results[t]["correlation"] <= 1.0


def test_insufficient_data_handling():
    """Test behavior when threshold leaves too few data points."""
    df_vsw, df_ey, timestamps = generate_test_data(n_points=100)

    # Very high threshold should leave very few points
    results = analyze_thresholds(df_vsw, df_ey, timestamps, thresholds=[900.0])

    assert "900.0" in results
    # Should have a note or NaN values if insufficient data
    assert results["900.0"]["n_samples"] < 10 or "note" in results["900.0"]


def test_run_sensitivity_sweep_defaults():
    """Test that run_sensitivity_sweep uses default thresholds."""
    df_vsw, df_ey, timestamps = generate_test_data(n_points=1000)

    results = run_sensitivity_sweep(df_vsw, df_ey, timestamps)

    # Should default to [400, 500, 600]
    assert "400.0" in results
    assert "500.0" in results
    assert "600.0" in results
