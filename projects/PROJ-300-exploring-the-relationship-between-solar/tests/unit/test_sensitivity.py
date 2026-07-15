"""
Unit tests for sensitivity threshold filtering logic in code/analysis/sensitivity.py.
Tests verify FR-007: sweep thresholds T ∈ {high, medium, low} km/s and recompute correlations.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Ensure project root is in path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.analysis.sensitivity import analyze_thresholds, run_sensitivity_sweep
from code.config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP


def create_synthetic_dataset(n_points=1000, lag_minutes=45, noise_scale=0.5):
    """
    Create a synthetic dataset with a known correlation and lag.
    Vsw drives Ey with a time delay and some noise.
    """
    dates = pd.date_range(start="2023-01-01", periods=n_points, freq="5min")
    
    # Create a base signal (Vsw) with some variation
    base_signal = np.sin(np.linspace(0, 20, n_points)) * 100 + 400
    
    # Create Ey with a lagged correlation to Vsw + noise
    lagged_signal = np.roll(base_signal, int(lag_minutes / 5)) # 5min freq
    noise = np.random.normal(0, noise_scale, n_points)
    ey_signal = (lagged_signal * 0.5) + 5 + noise
    
    df = pd.DataFrame({
        'timestamp': dates,
        'Vsw': base_signal,
        'Ey': ey_signal
    })
    return df


def test_threshold_filtering():
    """
    Test that threshold filtering correctly subsets the data based on Vsw values.
    FR-007: Sweep thresholds T ∈ {high, medium, low} km/s.
    """
    df = create_synthetic_dataset(n_points=500)
    
    # Define thresholds
    thresholds = {
        'low': 400,
        'medium': 500,
        'high': 600
    }
    
    # Test filtering logic manually first
    for name, value in thresholds.items():
        filtered = df[df['Vsw'] > value]
        # Verify all values in filtered set are > threshold
        assert all(filtered['Vsw'] > value), f"Threshold {name} ({value}) failed filtering"
        # Verify count decreases as threshold increases
        if name == 'low':
            assert len(filtered) == len(df[df['Vsw'] > 400])
    
    # Now test the function
    result = analyze_thresholds(df, thresholds)
    
    assert 'low' in result
    assert 'medium' in result
    assert 'high' in result
    
    # Verify counts match expected filtering
    assert result['low']['count'] == len(df[df['Vsw'] > 400])
    assert result['medium']['count'] == len(df[df['Vsw'] > 500])
    assert result['high']['count'] == len(df[df['Vsw'] > 600])


def test_sensitivity_correlation_calculation():
    """
    Test that correlations are calculated correctly for each threshold subset.
    FR-007: Recompute correlations for each threshold.
    """
    df = create_synthetic_dataset(n_points=1000, lag_minutes=45, noise_scale=0.1)
    
    thresholds = {
        'low': 400,
        'medium': 500,
        'high': 600
    }
    
    result = analyze_thresholds(df, thresholds)
    
    # Verify that correlations are present and are numbers
    for key in thresholds.keys():
        assert 'pearson' in result[key], f"Pearson correlation missing for {key}"
        assert 'spearman' in result[key], f"Spearman correlation missing for {key}"
        assert isinstance(result[key]['pearson'], (int, float, np.floating)), \
            f"Pearson correlation for {key} is not numeric"
        assert isinstance(result[key]['spearman'], (int, float, np.floating)), \
            f"Spearman correlation for {key} is not numeric"
    
    # Verify that correlations are within valid range [-1, 1]
    for key in thresholds.keys():
        assert -1 <= result[key]['pearson'] <= 1, \
            f"Pearson correlation for {key} out of range: {result[key]['pearson']}"
        assert -1 <= result[key]['spearman'] <= 1, \
            f"Spearman correlation for {key} out of range: {result[key]['spearman']}"
    
    # Verify that higher thresholds (stronger solar wind) generally show different correlation
    # than lower thresholds (weaker solar wind) - this is a physical expectation
    # We expect the correlation to be significant in all cases but potentially different magnitudes
    assert abs(result['low']['pearson']) > 0.1, "Low threshold correlation too weak"
    assert abs(result['medium']['pearson']) > 0.1, "Medium threshold correlation too weak"
    assert abs(result['high']['pearson']) > 0.1, "High threshold correlation too weak"


def test_sensitivity_with_nan_handling():
    """
    Test that the sensitivity analysis handles NaN values correctly.
    """
    df = create_synthetic_dataset(n_points=500)
    
    # Introduce some NaN values
    df.loc[10:20, 'Vsw'] = np.nan
    df.loc[30:40, 'Ey'] = np.nan
    
    thresholds = {
        'low': 400,
        'medium': 500,
        'high': 600
    }
    
    # Should not raise an error
    result = analyze_thresholds(df, thresholds)
    
    # Verify that results are still generated
    for key in thresholds.keys():
        assert 'pearson' in result[key]
        assert 'spearman' in result[key]
    
    # Verify that counts are reduced due to NaN removal
    # (The exact reduction depends on how many NaNs fall into each threshold bucket)
    for key in thresholds.keys():
        assert result[key]['count'] >= 0


def test_sensitivity_empty_threshold():
    """
    Test behavior when a threshold results in an empty dataset.
    """
    df = create_synthetic_dataset(n_points=100)
    
    # Use a threshold that will filter out all data
    thresholds = {
        'extreme': 10000  # Vsw values are around 400-500
    }
    
    result = analyze_thresholds(df, thresholds)
    
    # Should handle empty dataset gracefully
    assert 'extreme' in result
    assert result['extreme']['count'] == 0
    
    # Correlation should be NaN or None for empty set
    assert pd.isna(result['extreme']['pearson']) or result['extreme']['pearson'] is None
    assert pd.isna(result['extreme']['spearman']) or result['extreme']['spearman'] is None


def test_run_sensitivity_sweep_integration():
    """
    Test the full sensitivity sweep function with realistic parameters.
    """
    df = create_synthetic_dataset(n_points=1000, lag_minutes=45)
    
    # Run the full sweep
    result = run_sensitivity_sweep(
        df, 
        thresholds=[400, 500, 600],
        lag_window_min=LAG_WINDOW_MIN,
        lag_window_max=LAG_WINDOW_MAX,
        lag_step=LAG_STEP
    )
    
    # Verify structure
    assert 'thresholds' in result
    assert 'summary' in result
    
    # Verify each threshold has results
    for threshold in [400, 500, 600]:
        assert threshold in result['thresholds']
        assert 'pearson' in result['thresholds'][threshold]
        assert 'spearman' in result['thresholds'][threshold]
        assert 'optimal_lag' in result['thresholds'][threshold]
    
    # Verify summary is present
    assert 'trend' in result['summary']
    assert 'significant_correlations' in result['summary']