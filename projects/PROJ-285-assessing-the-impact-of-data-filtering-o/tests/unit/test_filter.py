"""
Unit tests for the filter module.
"""
import pytest
import pandas as pd
import numpy as np
from src.filter import filter_by_thresholds, generate_threshold_grid
from src.logging_config import ThresholdFilterError

def test_generate_threshold_grid_dimensions():
    """Test that the threshold grid has the expected dimensions."""
    snr_thresholds, morph_thresholds = generate_threshold_grid()
    
    # SNR should range from 5 to 20 inclusive (16 values)
    expected_snr_count = 16  # 5, 6, ..., 20
    assert len(snr_thresholds) == expected_snr_count
    assert snr_thresholds[0] == 5
    assert snr_thresholds[-1] == 20
    
    # Morph should range from 0.3 to 0.9 inclusive (7 values)
    expected_morph_count = 7  # 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9
    assert len(morph_thresholds) == expected_morph_count
    assert abs(morph_thresholds[0] - 0.3) < 1e-6
    assert abs(morph_thresholds[-1] - 0.9) < 1e-6

def test_filter_by_thresholds_basic():
    """Test basic filtering functionality."""
    # Create a simple test dataset
    data = {
        'snr': [5.0, 10.0, 15.0, 20.0, 25.0],
        'morph': [0.3, 0.5, 0.7, 0.9, 1.0]
    }
    df = pd.DataFrame(data)
    
    result = filter_by_thresholds(df)
    
    # Should have 16 * 7 = 112 rows
    assert len(result) == 112
    
    # Check that detection counts are non-negative integers
    assert (result['detection_count'] >= 0).all()
    assert result['detection_count'].dtype in [np.int64, np.int32, int]

def test_filter_by_thresholds_missing_values():
    """Test handling of missing values (NA/NaN)."""
    # Create a dataset with missing values
    data = {
        'snr': [5.0, np.nan, 15.0, None, 25.0],
        'morph': [0.3, 0.5, np.nan, 0.9, 1.0]
    }
    df = pd.DataFrame(data)
    
    # Should not raise an error
    result = filter_by_thresholds(df)
    
    # Should have 112 rows
    assert len(result) == 112
    
    # Detection counts should be based on non-missing values
    # Only 3 rows have both snr and morph values
    assert (result['detection_count'] <= 3).all()

def test_filter_by_thresholds_upper_bound():
    """Test that the grid includes a representative threshold value near the upper bound."""
    snr_thresholds, morph_thresholds = generate_threshold_grid()
    
    # SNR upper bound should be 20
    assert 20 in snr_thresholds
    
    # Morph upper bound should be 0.9
    assert 0.9 in morph_thresholds

def test_filter_by_thresholds_empty_dataframe():
    """Test filtering on an empty DataFrame."""
    df = pd.DataFrame(columns=['snr', 'morph'])
    
    result = filter_by_thresholds(df)
    
    # Should have 112 rows but all counts should be 0
    assert len(result) == 112
    assert (result['detection_count'] == 0).all()

def test_filter_by_thresholds_single_row():
    """Test filtering on a single row DataFrame."""
    data = {
        'snr': [15.0],
        'morph': [0.7]
    }
    df = pd.DataFrame(data)
    
    result = filter_by_thresholds(df)
    
    # Should have 112 rows
    assert len(result) == 112
    
    # For thresholds <= 15.0 and <= 0.7, count should be 1
    # For thresholds > 15.0 or > 0.7, count should be 0
    mask = (result['snr_threshold'] <= 15.0) & (result['morph_threshold'] <= 0.7)
    assert (result.loc[mask, 'detection_count'] == 1).all()
    assert (result.loc[~mask, 'detection_count'] == 0).all()