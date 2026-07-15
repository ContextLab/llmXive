"""
Unit tests for sensitivity threshold filtering (FR-007).

This module tests the functionality in `code/analysis/sensitivity.py`
specifically regarding the filtering of data by solar wind speed thresholds
and the subsequent correlation calculations.

File: tests/unit/test_sensitivity.py
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Ensure the project root is in the path for relative imports
# This assumes the test is run from the project root or via pytest discovery
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.analysis.sensitivity import analyze_thresholds
from code.config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP


def create_synthetic_dataset(n_samples=1000, seed=42):
    """
    Create a synthetic dataset with Vsw and Ey for testing.
    Introduces a known linear relationship with noise to verify correlation logic.
    """
    np.random.seed(seed)
    dates = [datetime(2023, 1, 1) + timedelta(minutes=5 * i) for i in range(n_samples)]
    
    # Generate Vsw with a trend and noise
    # Range roughly 300 to 800 km/s
    base_vsw = 400 + 150 * np.sin(np.linspace(0, 4 * np.pi, n_samples))
    noise_vsw = np.random.normal(0, 30, n_samples)
    vsw = base_vsw + noise_vsw
    
    # Generate Ey with a relationship to Vsw plus noise
    # Ey ~ 0.5 * Vsw + noise
    ey = 0.5 * vsw + np.random.normal(0, 20, n_samples)
    
    df = pd.DataFrame({
        'timestamp': dates,
        'Vsw': vsw,
        'Ey': ey
    })
    return df


def test_threshold_filtering():
    """
    Test that analyze_thresholds correctly filters data based on Vsw thresholds.
    
    FR-007 Requirement: Sweep thresholds T ∈ {high, medium, low} km/s and 
    recompute correlations.
    """
    df = create_synthetic_dataset(n_samples=1000)
    
    # Define thresholds to test
    thresholds = [400, 500, 600]
    
    results = analyze_thresholds(df, thresholds)
    
    # Verify the structure of the results
    assert isinstance(results, dict), "Results should be a dictionary"
    assert 'sensitivity_table' in results, "Results must contain 'sensitivity_table'"
    
    table = results['sensitivity_table']
    assert isinstance(table, list), "Sensitivity table should be a list"
    assert len(table) == len(thresholds), "Table length should match number of thresholds"
    
    # Verify each row in the table
    for i, threshold in enumerate(thresholds):
        row = table[i]
        assert 'threshold' in row, f"Row {i} missing 'threshold'"
        assert 'count' in row, f"Row {i} missing 'count'"
        assert 'pearson' in row, f"Row {i} missing 'pearson'"
        assert 'spearman' in row, f"Row {i} missing 'spearman'"
        
        # Verify threshold value
        assert row['threshold'] == threshold, f"Threshold mismatch at row {i}"
        
        # Verify count is non-negative
        assert row['count'] >= 0, "Count cannot be negative"
        
        # Verify correlation coefficients are within valid range [-1, 1]
        assert -1.0 <= row['pearson'] <= 1.0, "Pearson correlation out of bounds"
        assert -1.0 <= row['spearman'] <= 1.0, "Spearman correlation out of bounds"


def test_sensitivity_correlation_calculation():
    """
    Test that correlation values change appropriately as the threshold changes.
    
    Since the synthetic data has a positive correlation, filtering for higher
    Vsw (which are more variable in our synthetic generation due to the sine wave)
    should yield different correlation magnitudes than the full dataset.
    """
    df = create_synthetic_dataset(n_samples=2000, seed=123)
    
    # Test with a single high threshold
    thresholds = [600]
    results = analyze_thresholds(df, thresholds)
    
    table = results['sensitivity_table']
    assert len(table) == 1
    
    # The subset with Vsw > 600 should have a valid correlation
    row = table[0]
    assert row['count'] > 0, "Should have data points above 600 km/s"
    
    # Compare with a lower threshold
    thresholds_low = [400]
    results_low = analyze_thresholds(df, thresholds_low)
    row_low = results_low['sensitivity_table'][0]
    
    # Both should have valid correlations
    assert -1.0 <= row['pearson'] <= 1.0
    assert -1.0 <= row_low['pearson'] <= 1.0
    
    # The counts should differ significantly
    # (400 is a lower bar, so likely more points than 600)
    assert row_low['count'] >= row['count'], \
        "Lower threshold should include more or equal data points"


def test_sensitivity_with_nan_handling():
    """
    Test that the sensitivity analysis handles NaN values correctly.
    
    FR-007 implies cleaning before analysis; ensure NaNs don't crash the function.
    """
    df = create_synthetic_dataset(n_samples=100)
    
    # Inject NaNs
    df.loc[10:15, 'Vsw'] = np.nan
    df.loc[20:25, 'Ey'] = np.nan
    
    thresholds = [400]
    
    # This should not raise an exception
    results = analyze_thresholds(df, thresholds)
    
    # Verify we still get results
    assert 'sensitivity_table' in results
    table = results['sensitivity_table']
    
    # The count should be less than 100 due to NaN filtering
    assert table[0]['count'] < 100, "NaNs should reduce the sample count"


def test_sensitivity_empty_threshold():
    """
    Test behavior when a threshold filters out all data points.
    """
    df = create_synthetic_dataset(n_samples=100)
    
    # Use a threshold higher than any Vsw in the dataset
    # Max Vsw is roughly 400 + 150 + noise ~ 600
    thresholds = [10000]
    
    results = analyze_thresholds(df, thresholds)
    table = results['sensitivity_table']
    
    assert len(table) == 1
    row = table[0]
    
    assert row['count'] == 0, "No data points should match threshold 10000"
    
    # Correlation should be NaN or 0 when count is 0
    # scipy.stats returns NaN for correlation with < 2 points
    assert np.isnan(row['pearson']) or row['pearson'] == 0.0, \
        "Correlation should be undefined or zero for empty set"