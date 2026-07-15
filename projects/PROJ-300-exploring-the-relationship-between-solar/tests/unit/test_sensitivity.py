"""
Unit tests for sensitivity analysis functionality.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from analysis.sensitivity import analyze_thresholds

def create_synthetic_dataset(n_points=1000, seed=42):
    """Create a synthetic dataset for testing."""
    np.random.seed(seed)
    dates = pd.date_range(start="2023-01-01", periods=n_points, freq="5T")
    vsw = 400 + 100 * np.random.randn(n_points)
    # Ensure some values are above 500 and 600
    vsw = np.clip(vsw, 300, 800)
    ey = 0.5 * vsw + 10 * np.random.randn(n_points)
    
    df_vsw = pd.DataFrame({'timestamp': dates, 'Vsw': vsw})
    df_ey = pd.DataFrame({'timestamp': dates, 'Ey': ey})
    return df_vsw, df_ey

def test_threshold_filtering():
    """Test that thresholds correctly filter the data."""
    df_vsw, df_ey = create_synthetic_dataset()
    
    # Check that high threshold yields fewer samples
    results = analyze_thresholds(df_vsw, df_ey, [400, 600])
    
    assert len(results) == 2
    # 400 threshold should have more samples than 600
    assert results[0]['n_samples'] >= results[1]['n_samples']
    assert results[0]['status'] == 'ok'
    assert results[1]['status'] == 'ok'

def test_sensitivity_correlation_calculation():
    """Test that correlations are calculated and are numeric."""
    df_vsw, df_ey = create_synthetic_dataset()
    
    results = analyze_thresholds(df_vsw, df_ey, [400, 500, 600])
    
    for res in results:
        assert res['correlation'] is not None
        assert isinstance(res['correlation'], float)
        # Correlation should be between -1 and 1
        assert -1.0 <= res['correlation'] <= 1.0

def test_sensitivity_with_nan_handling():
    """Test that NaN values in input are handled gracefully."""
    df_vsw, df_ey = create_synthetic_dataset()
    # Inject NaNs
    df_vsw.loc[0:10, 'Vsw'] = np.nan
    df_ey.loc[0:10, 'Ey'] = np.nan
    
    results = analyze_thresholds(df_vsw, df_ey, [400])
    
    # Should still run without crashing
    assert len(results) == 1
    assert results[0]['status'] in ['ok', 'insufficient_data']

def test_sensitivity_empty_threshold():
    """Test behavior when a threshold leaves no data."""
    df_vsw, df_ey = create_synthetic_dataset()
    # Use a very high threshold that likely yields no data
    results = analyze_thresholds(df_vsw, df_ey, [10000])
    
    assert len(results) == 1
    assert results[0]['status'] == 'insufficient_data'
    assert results[0]['n_samples'] == 0