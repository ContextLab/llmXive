"""
test_interpolation.py

Unit tests for interpolation methods used in preprocessing.py.
Tests forward-fill vs linear interpolation on time-series data with missing values.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from preprocessing import interpolate_missing


def create_sample_timeseries(n_points=10, missing_indices=None):
    """Helper to create a sample time series with optional missing values."""
    if missing_indices is None:
        missing_indices = []
    dates = [datetime(2023, 1, 1) + timedelta(days=i) for i in range(n_points)]
    values = [float(i) for i in range(n_points)]
    for idx in missing_indices:
        values[idx] = np.nan
    return pd.DataFrame({"date": dates, "value": values}).set_index("date")


def test_linear_interpolation():
    """Test linear interpolation fills missing values correctly."""
    df = create_sample_timeseries(missing_indices=[2, 3])
    # Values: 0, 1, nan, nan, 4, 5, 6, 7, 8, 9
    # Linear interpolation between index 1 (val=1.0) and index 4 (val=4.0)
    # Index 2: 1.0 + (4.0 - 1.0) * (1/3) = 2.0
    # Index 3: 1.0 + (4.0 - 1.0) * (2/3) = 3.0
    # Note: Pandas default linear interpolation uses index distance.
    # Let's verify the actual behavior of the function we are testing.
    
    filled = interpolate_missing(df, method="linear")
    
    assert not filled["value"].isna().any(), "Linear interpolation should fill all NaN values"
    # Check specific values based on pandas linear interpolation logic
    # Index 2: distance from 1 is 1, distance from 4 is 2. Weighted avg: (1*2 + 4*1)/3 = 2.0
    # Index 3: distance from 1 is 2, distance from 4 is 1. Weighted avg: (1*1 + 4*2)/3 = 3.0
    assert filled.loc[filled.index[2], "value"] == 2.0
    assert filled.loc[filled.index[3], "value"] == 3.0


def test_ffill_interpolation():
    """Test forward-fill interpolation."""
    df = create_sample_timeseries(missing_indices=[2, 3])
    filled = interpolate_missing(df, method="ffill")
    
    assert not filled["value"].isna().any(), "Forward-fill should fill all NaN values"
    # Forward fill should carry the last valid value (1.0 at index 1) to indices 2 and 3
    assert filled.loc[filled.index[2], "value"] == 1.0
    assert filled.loc[filled.index[3], "value"] == 1.0


def test_no_missing_values():
    """Test interpolation on data with no missing values."""
    df = create_sample_timeseries(missing_indices=[])
    filled = interpolate_missing(df, method="linear")
    
    pd.testing.assert_frame_equal(df, filled)


def test_interpolation_edge_cases():
    """Test interpolation with edge cases like missing first or last values."""
    # Missing first value
    df_first = create_sample_timeseries(missing_indices=[0])
    filled_first = interpolate_missing(df_first, method="ffill")
    # ffill cannot fill the first value if there's no preceding value
    assert pd.isna(filled_first.loc[filled_first.index[0], "value"])
    
    # Missing last value
    df_last = create_sample_timeseries(missing_indices=[9])
    filled_last = interpolate_missing(df_last, method="bfill")
    # bfill cannot fill the last value if there's no succeeding value
    assert pd.isna(filled_last.loc[filled_last.index[9], "value"])
    
    # Linear interpolation on first/last
    filled_first_linear = interpolate_missing(df_first, method="linear")
    assert pd.isna(filled_first_linear.loc[filled_first_linear.index[0], "value"])
    
    filled_last_linear = interpolate_missing(df_last, method="linear")
    assert pd.isna(filled_last_linear.loc[filled_last_linear.index[9], "value"])


def test_invalid_method_raises_error():
    """Test that an invalid interpolation method raises a ValueError."""
    df = create_sample_timeseries(missing_indices=[2])
    with pytest.raises(ValueError, match="Unsupported interpolation method"):
        interpolate_missing(df, method="invalid_method")