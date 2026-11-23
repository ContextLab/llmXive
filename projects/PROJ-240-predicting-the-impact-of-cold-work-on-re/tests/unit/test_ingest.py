"""
Unit tests for T021: Outlier Clipping on Target Variable.
"""
import pytest
import pandas as pd
import numpy as np
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from ingest import clip_outliers_target

def test_clip_outliers_target_basic():
    """Test that outliers above 99th percentile are clipped."""
    # Create a dataset with clear outliers
    data = {
        'time_to_peak_min': [10, 20, 30, 40, 50, 1000]  # 1000 is an outlier
    }
    df = pd.DataFrame(data)
    
    # Clip at 99th percentile (which will be high but < 1000 given the distribution)
    # With 6 items, 99th percentile is effectively the max of the non-outlier set or interpolated
    # Let's force a scenario where we know the threshold
    # 10, 20, 30, 40, 50 -> 99th percentile is approx 50
    # 1000 should be clipped to ~50
    
    df_clipped, metrics = clip_outliers_target(df, percentile=0.99)
    
    # Check that the outlier was clipped
    assert df_clipped['time_to_peak_min'].max() <= 50.1  # Allow small float tolerance
    assert metrics['clipped_outliers_count'] > 0
    assert 'clipped_values_list' in metrics
    assert 'threshold_99th_percentile' in metrics

def test_clip_outliers_target_no_outliers():
    """Test that no clipping occurs if no outliers exist."""
    data = {
        'time_to_peak_min': [10, 20, 30, 40, 50]
    }
    df = pd.DataFrame(data)
    
    df_clipped, metrics = clip_outliers_target(df, percentile=0.99)
    
    # Should be identical
    pd.testing.assert_frame_equal(df, df_clipped)
    assert metrics['clipped_outliers_count'] == 0

def test_clip_outliers_target_missing_column():
    """Test that ValueError is raised if target column is missing."""
    data = {
        'other_col': [10, 20, 30]
    }
    df = pd.DataFrame(data)
    
    with pytest.raises(ValueError):
        clip_outliers_target(df, percentile=0.99)
