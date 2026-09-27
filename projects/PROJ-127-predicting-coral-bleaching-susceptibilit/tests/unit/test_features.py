import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from features import compute_lagged_features, compute_interaction_features, check_definitional_circularity, calculate_vif, filter_high_vif

def test_compute_lagged_features():
    """Test that lagged features are computed correctly."""
    # Create test data
    dates = pd.date_range(start='2020-01-01', periods=60, freq='D')
    data = {
        'date': dates,
        'sst': np.random.rand(60) * 2 + 25,  # SST around 25-27
        'dhw': np.random.rand(60) * 5
    }
    df = pd.DataFrame(data)
    
    # Compute lagged features
    df_lagged = compute_lagged_features(df, date_col='date', target_cols=['sst'])
    
    # Check that lagged column exists
    assert 'sst_30d_mean' in df_lagged.columns
    
    # Check that lagged values are reasonable (not NaN for most rows)
    assert df_lagged['sst_30d_mean'].notna().sum() > 30

def test_compute_interaction_features():
    """Test that interaction features are computed correctly."""
    # Create test data
    data = {
        'dhw': [1, 2, 3, 4, 5],
        'thermal_tolerance': [10, 20, 30, 40, 50]
    }
    df = pd.DataFrame(data)
    
    # Compute interaction features
    df_interaction = compute_interaction_features(df, col1='dhw', col2='thermal_tolerance')
    
    # Check that interaction column exists
    assert 'dhw_times_thermal_tolerance' in df_interaction.columns
    
    # Check values
    expected = [10, 40, 90, 160, 250]
    assert list(df_interaction['dhw_times_thermal_tolerance']) == expected

def test_check_definitional_circularity():
    """Test that definational circularity is detected and handled."""
    # Create test data with high correlation between DHW and SST
    sst = np.linspace(25, 30, 50)
    dhw = sst * 0.5 + np.random.rand(50) * 0.1  # High correlation
    
    data = {
        'date': pd.date_range(start='2020-01-01', periods=50, freq='D'),
        'sst': sst,
        'dhw': dhw
    }
    df = pd.DataFrame(data)
    
    # Check circularity
    df_circ = check_definitional_circularity(df, dhw_col='dhw', sst_col='sst')
    
    # Check that circularity flag is set
    assert 'circularity_detected' in df_circ.columns
    assert df_circ['circularity_detected'].any()
    
    # Check that DHW column is dropped
    assert 'dhw' not in df_circ.columns

def test_calculate_vif():
    """Test that VIF is calculated correctly."""
    # Create test data
    data = {
        'feature1': np.random.rand(100),
        'feature2': np.random.rand(100),
        'feature3': np.random.rand(100)
    }
    df = pd.DataFrame(data)
    
    # Calculate VIF
    vif_df = calculate_vif(df)
    
    # Check that VIF values are computed
    assert 'vif' in vif_df.columns
    assert len(vif_df) == 3
    
    # Check that VIF values are positive
    assert (vif_df['vif'] > 0).all()

def test_filter_high_vif():
    """Test that high VIF features are filtered correctly."""
    # Create test data with one high VIF feature
    np.random.seed(42)
    feature1 = np.random.rand(100)
    feature2 = feature1 + np.random.rand(100) * 0.1  # Highly correlated
    feature3 = np.random.rand(100)
    
    data = {
        'feature1': feature1,
        'feature2': feature2,
        'feature3': feature3
    }
    df = pd.DataFrame(data)
    
    # Create VIF DataFrame
    vif_df = pd.DataFrame({
        'feature': ['feature1', 'feature2', 'feature3'],
        'vif': [2.0, 10.0, 2.0]  # feature2 has high VIF
    })
    
    # Filter high VIF
    filtered_df = filter_high_vif(df, vif_df, threshold=5.0)
    
    # Check that high VIF feature is dropped
    assert 'feature2' not in filtered_df.columns
    assert 'feature1' in filtered_df.columns
    assert 'feature3' in filtered_df.columns

def test_main_function():
    """Test that main function runs without error (mocked)."""
    # This test ensures the main function structure is correct
    # Actual execution requires real data files
    from features import main
    import unittest.mock as mock
    
    # Mock file existence check
    with mock.patch('pathlib.Path.exists', return_value=True):
        with mock.patch('pandas.read_csv', return_value=pd.DataFrame({'dhw': [1], 'thermal_tolerance': [2], 'sst': [3]})):
            with mock.patch('pandas.DataFrame.to_csv'):
                # This should not raise an error
                try:
                    main()
                except Exception as e:
                    pytest.fail(f"main() raised an exception: {e}")
