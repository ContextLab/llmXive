import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path to import features
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from features import compute_lagged_features, compute_interaction_features, check_definitional_circularity, calculate_vif, filter_high_vif

def test_compute_lagged_features():
    """Test 30-day rolling mean SST calculation."""
    # Create a simple dataframe with dates and SST
    dates = [datetime(2023, 1, i) for i in range(1, 32)]
    sst_values = [25.0 + i * 0.1 for i in range(31)]
    df = pd.DataFrame({'date': dates, 'sst': sst_values})
    
    result = compute_lagged_features(df)
    
    assert 'sst_lag_30d' in result.columns
    assert len(result) == 31
    # The first value should be the first SST value (min_periods=1)
    assert result['sst_lag_30d'].iloc[0] == 25.0
    # Check a later value roughly (rolling mean)
    assert result['sst_lag_30d'].iloc[-1] > 25.0

def test_compute_interaction_features():
    """Test DHW * thermal_tolerance interaction."""
    df = pd.DataFrame({
        'dhw': [1.0, 2.0, 3.0],
        'thermal_tolerance': [1.5, 2.0, 2.5]
    })
    
    result = compute_interaction_features(df)
    
    assert 'dhw_thermal_interaction' in result.columns
    expected = [1.0*1.5, 2.0*2.0, 3.0*2.5]
    assert result['dhw_thermal_interaction'].tolist() == expected

def test_check_definitional_circularity():
    """Test circularity check logic."""
    df = pd.DataFrame({'dhw': [1.0], 'sst': [25.0]})
    is_circular, msg = check_definitional_circularity(df)
    
    assert is_circular is True
    assert "DHW is derived from SST" in msg

def test_calculate_vif():
    """Test VIF calculation."""
    # Create a dataset with some correlation
    np.random.seed(42)
    n = 100
    x1 = np.random.normal(0, 1, n)
    x2 = x1 * 0.5 + np.random.normal(0, 0.1, n) # Correlated with x1
    x3 = np.random.normal(0, 1, n) # Independent
    
    df = pd.DataFrame({'x1': x1, 'x2': x2, 'x3': x3})
    
    vif_result = calculate_vif(df)
    
    assert 'vif' in vif_result.columns
    assert 'feature' in vif_result.columns
    assert len(vif_result) == 3

def test_filter_high_vif():
    """Test filtering of high VIF features."""
    # Create a dataset where one feature is highly correlated with another
    np.random.seed(42)
    n = 100
    x1 = np.random.normal(0, 1, n)
    x2 = x1 * 0.99 + np.random.normal(0, 0.01, n) # Very high correlation
    x3 = np.random.normal(0, 1, n)
    
    df = pd.DataFrame({'x1': x1, 'x2': x2, 'x3': x3, 'target': np.random.randint(0, 2, n)})
    
    filtered_df = filter_high_vif(df, threshold=5.0)
    
    # One of the highly correlated features should be dropped
    assert 'x1' not in filtered_df.columns or 'x2' not in filtered_df.columns
    assert 'x3' in filtered_df.columns