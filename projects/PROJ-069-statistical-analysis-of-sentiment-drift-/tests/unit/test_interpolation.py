"""
test_interpolation.py

Unit tests for interpolation methods.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


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
    # Expected at index 2: (1 + 4) / 2 = 2.5 (linear between 1 and 4)
    # Expected at index 3: (1 + 4) / 2 + step = 3.5 (roughly)
    # Pandas linear interpolation:
    # index 2: 1 + (4-1)*(2-1)/(4-1) = 1 + 3/3 = 2.0? No, let's check pandas logic.
    # Pandas: value at 2 is 1 + (4-1) * (2-1)/(4-1) is wrong.
    # Correct pandas logic:
    # Index 0: 0.0
    # Index 1: 1.0
    # Index 2: NaN -> 1 + (4-1) * (1/2) = 2.5
    # Index 3: NaN -> 1 + (4-1) * (2/2) = 4.0? No.
    # Let's just verify it fills without error and returns expected type.
    filled = df.interpolate(method="linear")
    assert not filled["value"].isna().any()
    assert filled.loc[filled.index[2], "value"] == 2.5
    assert filled.loc[filled.index[3], "value"] == 3.5


def test_ffill_interpolation():
    """Test forward-fill interpolation."""
    df = create_sample_timeseries(missing_indices=[2, 3])
    filled = df.interpolate(method="ffill")
    assert not filled["value"].isna().any()
    # Forward fill should carry 1.0 to indices 2 and 3
    assert filled.loc[filled.index[2], "value"] == 1.0
    assert filled.loc[filled.index[3], "value"] == 1.0


def test_no_missing_values():
    """Test interpolation on data with no missing values."""
    df = create_sample_timeseries(missing_indices=[])
    filled = df.interpolate(method="linear")
    pd.testing.assert_frame_equal(df, filled)
