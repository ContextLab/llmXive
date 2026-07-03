"""
Unit tests for sensitivity threshold filtering (FR-007).
Verifies that the sensitivity table correctly reports correlation magnitude for each threshold.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from code.analysis.sensitivity import analyze_thresholds
from code.analysis.correlation import calculate_correlation
from code.data.lag import apply_lag_shift


def generate_synthetic_data(n_points=1000, lag_minutes=45, noise_scale=0.1):
    """
    Generate synthetic data with a known lag relationship between Vsw and Ey.
    Ey is a delayed version of Vsw plus some noise.
    """
    timestamps = pd.date_range(start="2023-01-01", periods=n_points, freq="1min")
    
    # Create a base signal for Vsw
    vsw_signal = 400 + 100 * np.sin(np.linspace(0, 10 * np.pi, n_points))
    vsw_signal += np.random.normal(0, 10, n_points)
    
    # Create Ey as a delayed version of Vsw (lagged by lag_minutes)
    lag_steps = lag_minutes  # Since freq is 1min
    ey_signal = np.roll(vsw_signal, lag_steps)
    ey_signal += np.random.normal(0, noise_scale * 100, n_points)
    
    # Create DataFrames
    df_vsw = pd.DataFrame({
        'timestamp': timestamps,
        'Vsw': vsw_signal
    })
    df_ey = pd.DataFrame({
        'timestamp': timestamps,
        'Ey': ey_signal
    })
    
    return df_vsw, df_ey


def test_threshold_filtering():
    """
    Test that analyze_thresholds correctly filters data based on Vsw thresholds.
    """
    # Generate synthetic data
    df_vsw, df_ey = generate_synthetic_data(n_points=2000, lag_minutes=45)
    
    # Define thresholds to test
    thresholds = [400, 500, 600]
    
    # Run sensitivity analysis
    results = analyze_thresholds(df_vsw, df_ey, thresholds, lag_minutes=45)
    
    # Verify results structure
    assert isinstance(results, dict)
    assert 'sensitivity_table' in results
    
    # Verify all thresholds are present
    for threshold in thresholds:
        assert threshold in results['sensitivity_table']
        
    # Verify each threshold result has required keys
    for threshold, data in results['sensitivity_table'].items():
        assert 'pearson' in data
        assert 'spearman' in data
        assert 'n_points' in data
        assert 'significant' in data


def test_sensitivity_correlation_calculation():
    """
    Test that correlation values are calculated correctly for each threshold.
    """
    # Generate synthetic data with a strong relationship
    df_vsw, df_ey = generate_synthetic_data(n_points=2000, lag_minutes=45, noise_scale=0.05)
    
    # Define thresholds
    thresholds = [400, 500, 600]
    
    # Run sensitivity analysis
    results = analyze_thresholds(df_vsw, df_ey, thresholds, lag_minutes=45)
    
    # Verify correlation values are reasonable (should be positive and significant)
    for threshold, data in results['sensitivity_table'].items():
        pearson_corr = data['pearson']
        spearman_corr = data['spearman']
        
        # Correlations should be between -1 and 1
        assert -1.0 <= pearson_corr <= 1.0
        assert -1.0 <= spearman_corr <= 1.0
        
        # With our synthetic data, correlations should be positive
        assert pearson_corr > 0.3, f"Pearson correlation too low for threshold {threshold}: {pearson_corr}"
        assert spearman_corr > 0.3, f"Spearman correlation too low for threshold {threshold}: {spearman_corr}"
        
        # Significant flag should be True for our synthetic data
        assert data['significant'] == True, f"Significance flag incorrect for threshold {threshold}"
        
        # Verify n_points is reasonable (should be less than total points)
        assert 0 < data['n_points'] < 2000, f"n_points invalid for threshold {threshold}: {data['n_points']}"


def test_sensitivity_with_realistic_thresholds():
    """
    Test that the sensitivity analysis works with realistic solar wind thresholds.
    """
    # Generate synthetic data
    df_vsw, df_ey = generate_synthetic_data(n_points=1000, lag_minutes=45)
    
    # Realistic thresholds for solar wind speed (km/s)
    realistic_thresholds = [300, 400, 500, 600, 700]
    
    # Run sensitivity analysis
    results = analyze_thresholds(df_vsw, df_ey, realistic_thresholds, lag_minutes=45)
    
    # Verify all thresholds are present
    for threshold in realistic_thresholds:
        assert threshold in results['sensitivity_table'], f"Threshold {threshold} missing from results"
        
    # Verify the number of data points decreases as threshold increases
    # (higher thresholds filter out more data)
    prev_n_points = float('inf')
    for threshold in sorted(realistic_thresholds):
        n_points = results['sensitivity_table'][threshold]['n_points']
        assert n_points <= prev_n_points, f"n_points should decrease or stay same as threshold increases: {threshold}"
        prev_n_points = n_points
    
    # Verify that higher thresholds have fewer data points
    assert results['sensitivity_table'][700]['n_points'] <= results['sensitivity_table'][300]['n_points']


def test_sensitivity_with_no_data_above_threshold():
    """
    Test that the function handles cases where no data exceeds a high threshold.
    """
    # Generate synthetic data with max Vsw around 500 km/s
    df_vsw, df_ey = generate_synthetic_data(n_points=1000, lag_minutes=45)
    
    # Set a very high threshold that no data exceeds
    high_thresholds = [1000, 2000]
    
    # Run sensitivity analysis
    results = analyze_thresholds(df_vsw, df_ey, high_thresholds, lag_minutes=45)
    
    # Verify results structure
    assert isinstance(results, dict)
    assert 'sensitivity_table' in results
    
    # For thresholds with no data, correlations should be NaN or 0, and significant should be False
    for threshold in high_thresholds:
        data = results['sensitivity_table'][threshold]
        assert data['n_points'] == 0, f"Expected 0 points for threshold {threshold}, got {data['n_points']}"
        # Correlation should be NaN or 0 when no data
        assert np.isnan(data['pearson']) or data['pearson'] == 0, f"Unexpected correlation for threshold {threshold}"
        assert data['significant'] == False, f"Should not be significant for threshold {threshold}"