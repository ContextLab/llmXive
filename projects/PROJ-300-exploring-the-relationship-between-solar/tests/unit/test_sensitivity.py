"""
Unit tests for analysis/sensitivity.py (FR-007).
File: tests/unit/test_sensitivity.py
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from code.analysis.sensitivity import analyze_thresholds, run_sensitivity_sweep


def create_mock_data(n_points=100, start_time=None):
    """Helper to create mock aligned dataframes."""
    if start_time is None:
        start_time = datetime(2023, 1, 1)
    
    timestamps = [start_time + timedelta(minutes=i*5) for i in range(n_points)]
    
    # Create Vsw with some variation
    vsw_values = np.random.uniform(300, 700, n_points)
    # Create Ey with some correlation to Vsw for testing
    ey_values = 0.5 * vsw_values + np.random.normal(0, 10, n_points)
    
    df_vsw = pd.DataFrame({
        'timestamp': timestamps,
        'Vsw': vsw_values,
        'Bz': np.random.uniform(-10, 10, n_points)
    })
    
    df_ey = pd.DataFrame({
        'timestamp': timestamps,
        'Ey': ey_values
    })
    
    return df_vsw, df_ey


def test_threshold_filtering():
    """
    Test that analyze_thresholds correctly filters data based on Vsw thresholds.
    """
    df_vsw, df_ey = create_mock_data(n_points=1000)
    
    # Test with a high threshold that should leave some data
    results = analyze_thresholds(df_vsw, df_ey, thresholds=[600.0])
    
    assert "T_600" in results
    assert results["T_600"]["count"] > 0
    assert results["T_600"]["count"] < 1000 # Should be a subset
    
    # Verify correlation values are numeric (not None)
    assert isinstance(results["T_600"]["pearson"], float)
    assert isinstance(results["T_600"]["spearman"], float)


def test_sensitivity_correlation_calculation():
    """
    Test that correlations are calculated for multiple thresholds.
    """
    df_vsw, df_ey = create_mock_data(n_points=1000)
    
    thresholds = [400.0, 500.0, 600.0]
    results = analyze_thresholds(df_vsw, df_ey, thresholds=thresholds)
    
    assert len(results) == 3
    
    for t in thresholds:
        key = f"T_{int(t)}"
        assert key in results
        # As count increases (lower threshold), correlation might change,
        # but it must be a valid float.
        assert results[key]["pearson"] is not None
        assert results[key]["spearman"] is not None
        assert results[key]["optimal_lag"] is not None


def test_empty_result_handling():
    """
    Test behavior when a threshold filters out all data.
    """
    df_vsw, df_ey = create_mock_data(n_points=100)
    # Ensure max Vsw is low
    df_vsw['Vsw'] = df_vsw['Vsw'] * 0.1 + 100 # Max around 170
    
    results = analyze_thresholds(df_vsw, df_ey, thresholds=[500.0])
    
    assert "T_500" in results
    assert results["T_500"]["count"] == 0
    assert results["T_500"]["pearson"] is None
    assert "note" in results["T_500"]


def test_run_sensitivity_sweep():
    """
    Test the wrapper function run_sensitivity_sweep.
    """
    df_vsw, df_ey = create_mock_data(n_points=500)
    
    report = run_sensitivity_sweep(df_vsw, df_ey)
    
    assert "sensitivity_table" in report
    assert "status" in report
    assert report["status"] == "success"
    assert len(report["sensitivity_table"]) == 3 # Default 3 thresholds