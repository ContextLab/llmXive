"""
Unit tests for sensitivity analysis (FR-007).
File path: projects/PROJ-300-exploring-the-relationship-between-solar/tests/unit/test_sensitivity.py
"""
import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from code.analysis.sensitivity import analyze_thresholds, run_sensitivity_sweep
from code.analysis.correlation import calculate_correlation
from code.analysis.lag_search import find_optimal_lag

def create_dummy_data(n_points=1000, start_date=None):
    """Create dummy aligned data for testing."""
    if start_date is None:
        start_date = datetime(2023, 1, 1)
    
    timestamps = [start_date + timedelta(minutes=i*5) for i in range(n_points)]
    # Create Vsw with some variation
    vsw_values = 400 + 100 * np.random.randn(n_points)
    vsw_values = np.clip(vsw_values, 300, 800) # realistic range
    
    # Create Ey correlated with Vsw for testing
    ey_values = 0.5 * vsw_values + 50 * np.random.randn(n_points)
    
    df_vsw = pd.DataFrame({
        'timestamp': timestamps,
        'Vsw': vsw_values,
        'Bz': np.random.randn(n_points)
    })
    
    df_ey = pd.DataFrame({
        'timestamp': timestamps,
        'Ey': ey_values
    })
    
    return df_vsw, df_ey

def test_threshold_filtering():
    """Test that thresholds correctly filter the data."""
    df_vsw, df_ey = create_dummy_data()
    
    thresholds = [400, 500, 600]
    results = analyze_thresholds(df_vsw, df_ey, thresholds)
    
    assert len(results) == 3
    assert '400' in results
    assert '500' in results
    assert '600' in results
    
    # Higher thresholds should have fewer samples
    assert results['400']['n_samples'] >= results['500']['n_samples']
    assert results['500']['n_samples'] >= results['600']['n_samples']

def test_sensitivity_correlation_calculation():
    """Test that correlations are calculated for each threshold."""
    df_vsw, df_ey = create_dummy_data()
    
    thresholds = [400, 500, 600]
    results = analyze_thresholds(df_vsw, df_ey, thresholds)
    
    for t_str, data in results.items():
        if data['n_samples'] >= 10:
            assert data['pearson'] is not None
            assert data['spearman'] is not None
            assert -1 <= data['pearson'] <= 1
            assert -1 <= data['spearman'] <= 1

def test_run_sensitivity_sweep_defaults():
    """Test the default sweep with 400, 500, 600."""
    df_vsw, df_ey = create_dummy_data()
    
    sweep_results = run_sensitivity_sweep(df_vsw, df_ey)
    
    assert 'thresholds_tested' in sweep_results
    assert sweep_results['thresholds_tested'] == [400, 500, 600]
    assert 'results' in sweep_results
    assert len(sweep_results['results']) == 3
    
    # Check structure of each result entry
    for entry in sweep_results['results']:
        assert 'threshold_km_s' in entry
        assert 'n_samples' in entry
        assert 'optimal_lag_min' in entry
        assert 'pearson_correlation' in entry
        assert 'spearman_correlation' in entry
        assert 'is_significant' in entry

def test_insufficient_data_handling():
    """Test handling of thresholds that leave too little data."""
    # Create a small dataset
    df_vsw, df_ey = create_dummy_data(n_points=20)
    
    # Set a high threshold that will filter out most data
    thresholds = [750] # Likely to leave very few points
    results = analyze_thresholds(df_vsw, df_ey, thresholds)
    
    # Should handle gracefully, either with 0 samples or a reason
    assert '750' in results
    # If n_samples is 0, it should have a reason
    if results['750']['n_samples'] == 0:
        assert 'reason' in results['750']

def test_custom_thresholds():
    """Test with custom thresholds."""
    df_vsw, df_ey = create_dummy_data()
    custom_thresholds = [350, 450, 550, 650]
    
    results = analyze_thresholds(df_vsw, df_ey, custom_thresholds)
    
    assert len(results) == 4
    for t in custom_thresholds:
        assert str(t) in results
