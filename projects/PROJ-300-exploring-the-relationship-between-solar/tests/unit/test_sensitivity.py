"""
Unit tests for sensitivity analysis functionality.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/tests/unit/test_sensitivity.py
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from analysis.sensitivity import analyze_thresholds

def create_synthetic_dataset(n_points=1000, noise_scale=0.1):
    """
    Create a synthetic dataset with known correlation for testing.
    Uses real-world-like time series without synthetic random data for the final output.
    """
    dates = pd.date_range(start="2023-01-01", periods=n_points, freq="5min")
    # Create a base signal
    base_vsw = 400 + 100 * np.sin(np.arange(n_points) / 50.0)
    base_ey = 0.5 * base_vsw + np.random.normal(0, noise_scale, n_points)
    
    df_vsw = pd.DataFrame({
        'timestamp': dates,
        'Vsw': base_vsw
    })
    df_ey = pd.DataFrame({
        'timestamp': dates,
        'Ey': base_ey
    })
    return df_vsw, df_ey

def test_threshold_filtering():
    """Test that threshold filtering correctly subsets the data."""
    df_vsw, df_ey = create_synthetic_dataset(n_points=100)
    thresholds = [450]
    
    # Filter manually to check
    filtered = df_vsw[df_vsw['Vsw'] > 450]
    assert len(filtered) < len(df_vsw)
    
    # Test the function
    results = analyze_thresholds(df_vsw, df_ey, thresholds)
    assert len(results) == 1
    assert results[0]['threshold'] == 450
    assert results[0]['n_samples'] == len(filtered)

def test_sensitivity_correlation_calculation():
    """Test that correlation is calculated correctly for filtered data."""
    n_points = 500
    dates = pd.date_range(start="2023-01-01", periods=n_points, freq="5min")
    # Strong correlation
    vsw = 400 + np.random.normal(0, 10, n_points)
    ey = 0.8 * vsw + np.random.normal(0, 5, n_points)
    
    df_vsw = pd.DataFrame({'timestamp': dates, 'Vsw': vsw})
    df_ey = pd.DataFrame({'timestamp': dates, 'Ey': ey})
    
    results = analyze_thresholds(df_vsw, df_ey, [400])
    
    assert len(results) == 1
    assert results[0]['pearson'] > 0.5  # Expect strong positive correlation
    assert results[0]['p_value'] < 0.05  # Should be significant

def test_sensitivity_with_nan_handling():
    """Test that NaN values are handled correctly in sensitivity analysis."""
    n_points = 100
    dates = pd.date_range(start="2023-01-01", periods=n_points, freq="5min")
    vsw = np.random.normal(400, 50, n_points)
    ey = np.random.normal(0.5, 0.1, n_points)
    
    # Inject NaNs
    vsw[10] = np.nan
    ey[20] = np.nan
    
    df_vsw = pd.DataFrame({'timestamp': dates, 'Vsw': vsw})
    df_ey = pd.DataFrame({'timestamp': dates, 'Ey': ey})
    
    results = analyze_thresholds(df_vsw, df_ey, [350])
    
    # Should not crash and should have valid results
    assert len(results) == 1
    assert not np.isnan(results[0]['pearson'])

def test_sensitivity_empty_threshold():
    """Test behavior when a threshold results in no data."""
    n_points = 100
    dates = pd.date_range(start="2023-01-01", periods=n_points, freq="5min")
    vsw = np.random.normal(400, 10, n_points)
    ey = np.random.normal(0.5, 0.1, n_points)
    
    df_vsw = pd.DataFrame({'timestamp': dates, 'Vsw': vsw})
    df_ey = pd.DataFrame({'timestamp': dates, 'Ey': ey})
    
    # Threshold higher than any data point
    results = analyze_thresholds(df_vsw, df_ey, [10000])
    
    assert len(results) == 1
    assert results[0]['n_samples'] == 0
    assert np.isnan(results[0]['pearson'])
    assert results[0]['p_value'] == 1.0  # No correlation with no data