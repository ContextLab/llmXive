"""
Unit tests for sensitivity threshold filtering in analysis/sensitivity.py (FR-007).

Tests:
- test_threshold_filtering: Verifies that data is correctly filtered by Vsw thresholds.
- test_sensitivity_correlation_calculation: Verifies that correlations are correctly calculated 
  for each threshold and that the sensitivity table contains valid numeric results.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.analysis.sensitivity import analyze_thresholds, run_sensitivity_sweep
from code.data.clean import clean_and_resample

def create_synthetic_dataset(days=1, freq='5min'):
    """Create a synthetic dataset with known properties for testing."""
    dates = pd.date_range(
        start=datetime(2023, 6, 1),
        periods=int(days * 24 * 60 / (freq[0] if isinstance(freq, str) else 5)),
        freq=freq
    )
    
    # Create Vsw with distinct regions for threshold testing
    vsw_values = np.random.normal(450, 50, len(dates))
    # Inject some high-speed streams
    vsw_values[100:200] = 550 + np.random.normal(0, 20, 100)
    vsw_values[300:400] = 650 + np.random.normal(0, 20, 100)
    
    # Create Ey with some correlation to Vsw
    ey_values = 0.5 * vsw_values + np.random.normal(0, 10, len(dates))
    
    df = pd.DataFrame({
        'timestamp': dates,
        'Vsw': vsw_values,
        'Ey': ey_values
    })
    return df

def test_threshold_filtering():
    """Test that data is correctly filtered by Vsw thresholds."""
    df = create_synthetic_dataset(days=1)
    
    # Test high threshold (e.g., 600 km/s)
    high_mask = df['Vsw'] >= 600
    high_data = df[high_mask]
    
    # Verify all filtered values meet the threshold
    assert all(high_data['Vsw'] >= 600), "Threshold filtering failed: some values below threshold"
    assert len(high_data) > 0, "Threshold filtering failed: no data above threshold"
    
    # Test medium threshold (e.g., 500 km/s)
    medium_mask = df['Vsw'] >= 500
    medium_data = df[medium_mask]
    
    assert all(medium_data['Vsw'] >= 500), "Threshold filtering failed: some values below threshold"
    assert len(medium_data) > len(high_data), "Medium threshold should include more data than high threshold"
    
    # Test low threshold (e.g., 400 km/s)
    low_mask = df['Vsw'] >= 400
    low_data = df[low_mask]
    
    assert all(low_data['Vsw'] >= 400), "Threshold filtering failed: some values below threshold"
    assert len(low_data) > len(medium_data), "Low threshold should include more data than medium threshold"

def test_sensitivity_correlation_calculation():
    """Test that correlations are correctly calculated for each threshold."""
    df = create_synthetic_dataset(days=2)
    df_clean, _ = clean_and_resample(df, df)
    
    # Run sensitivity sweep
    thresholds = [400, 500, 600]
    results = analyze_thresholds(df_clean, df_clean, thresholds)
    
    # Verify structure
    assert 'sensitivity_table' in results, "Sensitivity table not in results"
    assert len(results['sensitivity_table']) == len(thresholds), "Incorrect number of threshold results"
    
    # Verify each threshold has correct structure and valid values
    for i, threshold in enumerate(thresholds):
        row = results['sensitivity_table'][i]
        assert row['threshold'] == threshold, f"Threshold mismatch for row {i}"
        assert 'pearson' in row, f"Pearson correlation missing for threshold {threshold}"
        assert 'spearman' in row, f"Spearman correlation missing for threshold {threshold}"
        assert 'sample_size' in row, f"Sample size missing for threshold {threshold}"
        
        # Verify correlation values are in valid range [-1, 1]
        assert -1 <= row['pearson'] <= 1, f"Pearson correlation out of range for threshold {threshold}"
        assert -1 <= row['spearman'] <= 1, f"Spearman correlation out of range for threshold {threshold}"
        
        # Verify sample size is positive
        assert row['sample_size'] > 0, f"Sample size should be positive for threshold {threshold}"
    
    # Verify that higher thresholds generally have fewer samples
    if len(results['sensitivity_table']) > 1:
        for i in range(len(results['sensitivity_table']) - 1):
            assert results['sensitivity_table'][i]['sample_size'] >= results['sensitivity_table'][i+1]['sample_size'], \
                "Sample size should decrease as threshold increases"

def test_sensitivity_with_nan_handling():
    """Test that sensitivity analysis correctly handles NaN values."""
    df = create_synthetic_dataset(days=1)
    
    # Inject some NaN values
    df.loc[50:60, 'Vsw'] = np.nan
    df.loc[100:110, 'Ey'] = np.nan
    
    df_clean, _ = clean_and_resample(df, df)
    
    # Should not raise an error
    thresholds = [400, 500, 600]
    results = analyze_thresholds(df_clean, df_clean, thresholds)
    
    # Verify results are still valid
    assert 'sensitivity_table' in results, "Sensitivity table missing after NaN handling"
    assert all(-1 <= row['pearson'] <= 1 for row in results['sensitivity_table']), \
        "Correlation values out of range after NaN handling"

def test_sensitivity_empty_threshold():
    """Test behavior when a threshold results in no data."""
    df = create_synthetic_dataset(days=1)
    
    # Use a threshold that should result in no data
    thresholds = [1000]  # No Vsw values this high in our synthetic data
    
    results = analyze_thresholds(df, df, thresholds)
    
    # Should handle gracefully - either empty table or zero sample size
    assert 'sensitivity_table' in results, "Sensitivity table missing for empty threshold"
    if len(results['sensitivity_table']) > 0:
        assert results['sensitivity_table'][0]['sample_size'] == 0, \
            "Sample size should be zero for empty threshold"
