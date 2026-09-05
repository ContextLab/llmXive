"""
Unit tests for T033: Correlation Analysis.
Validates Pearson correlation calculation and plot generation logic.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from correlation_analysis import (
    calculate_pearson_correlation,
    load_roi_betas,
    load_learning_rate_slopes
)

def test_pearson_correlation_calculation():
    """
    Test that the correlation function returns expected values for a known dataset.
    """
    # Create synthetic but deterministic data
    np.random.seed(42)
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y = np.array([2.1, 3.9, 6.2, 8.1, 9.8]) # Strong positive correlation
    
    results = calculate_pearson_correlation(pd.Series(x), pd.Series(y))
    
    assert 'r' in results
    assert 'p_value' in results
    assert 'n' in results
    assert results['n'] == 5
    assert 0.9 < results['r'] < 1.0, f"Expected r ~0.99, got {results['r']}"
    assert results['p_value'] < 0.05, "Expected significant p-value"
    assert results['ci_95_lower'] < results['r'] < results['ci_95_upper']

def test_pearson_correlation_no_correlation():
    """
    Test correlation with uncorrelated data.
    """
    np.random.seed(123)
    x = np.random.rand(20)
    y = np.random.rand(20)
    
    results = calculate_pearson_correlation(pd.Series(x), pd.Series(y))
    
    # With random data, r should be close to 0 and p > 0.05 (usually)
    assert abs(results['r']) < 0.5, "Random data should not have strong correlation"
    assert results['n'] == 20

def test_pearson_correlation_insufficient_data():
    """
    Test behavior with insufficient data points (< 3).
    """
    x = pd.Series([1.0, 2.0])
    y = pd.Series([3.0, 4.0])
    
    results = calculate_pearson_correlation(x, y)
    
    assert np.isnan(results['r'])
    assert np.isnan(results['p_value'])
    assert results['n'] == 2

def test_load_roi_betas_missing_file():
    """
    Test that load_roi_betas raises FileNotFoundError for missing file.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        missing_path = Path(tmpdir) / "nonexistent.csv"
        try:
            load_roi_betas(missing_path)
            assert False, "Expected FileNotFoundError"
        except FileNotFoundError:
            pass

def test_load_learning_rate_slopes_missing_file():
    """
    Test that load_learning_rate_slopes raises FileNotFoundError for missing file.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        missing_path = Path(tmpdir) / "nonexistent.csv"
        try:
            load_learning_rate_slopes(missing_path)
            assert False, "Expected FileNotFoundError"
        except FileNotFoundError:
            pass

def test_load_data_wrong_columns():
    """
    Test that loading data with wrong columns raises ValueError.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create file with wrong columns
        wrong_df = pd.DataFrame({'wrong_col': [1, 2, 3]})
        path = Path(tmpdir) / "wrong.csv"
        wrong_df.to_csv(path, index=False)
        
        try:
            load_roi_betas(path)
            assert False, "Expected ValueError"
        except ValueError:
            pass

if __name__ == "__main__":
    test_pearson_correlation_calculation()
    test_pearson_correlation_no_correlation()
    test_pearson_correlation_insufficient_data()
    test_load_roi_betas_missing_file()
    test_load_learning_rate_slopes_missing_file()
    test_load_data_wrong_columns()
    print("All tests passed.")