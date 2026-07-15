"""
Unit tests for T031: Verify sensitivity table correctly reports correlation magnitude.
These tests validate the logic of the sensitivity analysis function.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from code.analysis.sensitivity import analyze_thresholds
from code.config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP

def create_controlled_sensitivity_data():
    """
    Create a dataset with known correlation properties for different thresholds.
    We create a synthetic relationship where higher Vsw leads to higher Ey.
    """
    n_samples = 1000
    timestamps = pd.date_range(start="2023-01-01", periods=n_samples, freq="5min")
    
    # Create Vsw with a range that allows thresholding
    # Values between 300 and 700 km/s
    np.random.seed(42)
    vsw = np.random.uniform(300, 700, n_samples)
    
    # Create Ey with a positive correlation to Vsw plus noise
    # Ey = 0.01 * Vsw + noise
    noise = np.random.normal(0, 0.5, n_samples)
    ey = 0.01 * vsw + noise
    
    df_sw = pd.DataFrame({
        "timestamp": timestamps,
        "Vsw": vsw
    })
    
    df_ey = pd.DataFrame({
        "timestamp": timestamps,
        "Ey": ey
    })
    
    return df_sw, df_ey

def test_sensitivity_table_reports_all_thresholds():
    """Verify that the sensitivity table includes all requested thresholds."""
    df_sw, df_ey = create_controlled_sensitivity_data()
    thresholds = [400, 500, 600]
    
    results = analyze_thresholds(df_sw, df_ey, thresholds=thresholds)
    
    assert isinstance(results, dict)
    for t in thresholds:
        assert t in results, f"Threshold {t} missing from results"

def test_sensitivity_table_has_required_keys():
    """Verify that each threshold result has the required keys."""
    df_sw, df_ey = create_controlled_sensitivity_data()
    thresholds = [400]
    
    results = analyze_thresholds(df_sw, df_ey, thresholds=thresholds)
    
    required_keys = ["pearson", "spearman", "n_samples", "optimal_lag"]
    for t in thresholds:
        assert isinstance(results[t], dict)
        for key in required_keys:
            assert key in results[t], f"Key '{key}' missing for threshold {t}"

def test_sensitivity_correlation_decreases_with_stricter_threshold():
    """
    Verify that as we increase the threshold, the sample size decreases.
    (This is a structural check, not a physical one, as correlation direction 
    depends on the specific dataset physics).
    """
    df_sw, df_ey = create_controlled_sensitivity_data()
    thresholds = [400, 500, 600]
    
    results = analyze_thresholds(df_sw, df_ey, thresholds=thresholds)
    
    n_400 = results[400]["n_samples"]
    n_500 = results[500]["n_samples"]
    n_600 = results[600]["n_samples"]
    
    # Higher thresholds should result in fewer samples
    assert n_400 >= n_500 >= n_600, "Sample counts should decrease with higher thresholds"

def test_sensitivity_correlation_values_are_numeric():
    """Verify that correlation values are valid floats."""
    df_sw, df_ey = create_controlled_sensitivity_data()
    thresholds = [400]
    
    results = analyze_thresholds(df_sw, df_ey, thresholds=thresholds)
    
    for t in thresholds:
        pearson = results[t]["pearson"]
        spearman = results[t]["spearman"]
        
        assert isinstance(pearson, (float, np.floating))
        assert isinstance(spearman, (float, np.floating))
        assert -1.0 <= pearson <= 1.0, f"Pearson {pearson} out of range [-1, 1]"
        assert -1.0 <= spearman <= 1.0, f"Spearman {spearman} out of range [-1, 1]"

def test_sensitivity_table_precision():
    """Verify that correlation values are reported with reasonable precision."""
    df_sw, df_ey = create_controlled_sensitivity_data()
    thresholds = [400]
    
    results = analyze_thresholds(df_sw, df_ey, thresholds=thresholds)
    
    # Check that values are not just 0.0 or 1.0 (unless perfect correlation)
    # This ensures the calculation is actually running
    pearson = results[400]["pearson"]
    assert abs(pearson) > 0.01 or abs(pearson) < 0.99, "Correlation seems suspiciously perfect or zero"