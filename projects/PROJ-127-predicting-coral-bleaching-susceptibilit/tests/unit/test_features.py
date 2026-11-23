import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from features import (
    compute_lagged_features,
    compute_interaction_features,
    check_definitional_circularity,
    calculate_vif,
    filter_high_vif
)

@pytest.fixture
def sample_df():
    """Create a sample DataFrame for testing."""
    data = {
        'reef_id': ['R1', 'R1', 'R1', 'R2', 'R2', 'R2'],
        'date': pd.to_datetime(['2023-01-01', '2023-01-08', '2023-01-15', '2023-01-01', '2023-01-08', '2023-01-15']),
        'SST': [28.5, 29.0, 29.5, 27.0, 27.5, 28.0],
        'DHW': [1.0, 2.0, 3.0, 0.5, 1.0, 1.5],
        'thermal_tolerance': [2.5, 2.5, 2.5, 3.0, 3.0, 3.0],
        'bleaching_label': [0, 1, 1, 0, 0, 1]
    }
    return pd.DataFrame(data)

def test_compute_lagged_features(sample_df):
    """Test lagged feature computation."""
    result = compute_lagged_features(sample_df, 'SST', [1, 2], 'date')
    
    # Check that lag columns exist
    assert 'SST_lag_1' in result.columns
    assert 'SST_lag_2' in result.columns
    
    # Check values (first row should be NaN for lags)
    assert pd.isna(result.loc[0, 'SST_lag_1'])
    assert pd.isna(result.loc[1, 'SST_lag_1'])  # Should be SST from previous row in same reef
    
    # Check specific values
    assert result.loc[1, 'SST_lag_1'] == 28.5  # SST from previous row in R1
    assert result.loc[2, 'SST_lag_2'] == 28.5  # SST from 2 rows back in R1

def test_compute_interaction_features(sample_df):
    """Test interaction feature computation."""
    result = compute_interaction_features(sample_df, 'DHW', 'thermal_tolerance')
    
    # Check that interaction column exists
    assert 'DHW_x_thermal_tolerance' in result.columns
    
    # Check values
    expected = sample_df['DHW'] * sample_df['thermal_tolerance']
    pd.testing.assert_series_equal(result['DHW_x_thermal_tolerance'], expected)

def test_check_definitional_circularity(sample_df):
    """Test circularity check."""
    features = ['SST', 'DHW', 'thermal_tolerance']
    result = check_definitional_circularity(sample_df, features)
    
    # Check that circularity is detected
    assert len(result['circular_pairs']) > 0
    assert ('SST', 'DHW') in result['circular_pairs']
    assert len(result['warnings']) > 0

def test_calculate_vif(sample_df):
    """Test VIF calculation."""
    features = ['SST', 'DHW', 'thermal_tolerance', 'DHW_x_thermal_tolerance']
    # Add interaction column if not exists
    if 'DHW_x_thermal_tolerance' not in sample_df.columns:
        sample_df['DHW_x_thermal_tolerance'] = sample_df['DHW'] * sample_df['thermal_tolerance']
    
    result = calculate_vif(sample_df, features)
    
    # Check result structure
    assert 'feature' in result.columns
    assert 'vif' in result.columns
    assert len(result) == len(features)
    
    # Check VIF values are positive
    assert all(result['vif'] > 0)

def test_filter_high_vif():
    """Test filtering of high VIF features."""
    vif_data = pd.DataFrame({
        'feature': ['f1', 'f2', 'f3', 'f4'],
        'vif': [2.0, 4.5, 6.0, 8.0]
    })
    
    kept, dropped = filter_high_vif(vif_data, threshold=5.0)
    
    assert kept == ['f1', 'f2']
    assert dropped == ['f3', 'f4']

def test_filter_high_vif_threshold():
    """Test filtering with different thresholds."""
    vif_data = pd.DataFrame({
        'feature': ['f1', 'f2', 'f3'],
        'vif': [3.0, 5.0, 5.1]
    })
    
    kept, dropped = filter_high_vif(vif_data, threshold=5.0)
    
    assert kept == ['f1', 'f2']
    assert dropped == ['f3']
