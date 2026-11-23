import pytest
import pandas as pd
from pathlib import Path
import numpy as np
from code.data.preprocessing import fill_gaps, detect_cycle_boundaries

@pytest.fixture
def sample_gsn_data():
    """Create a sample GSN DataFrame with gaps."""
    dates = pd.date_range(start='2000-01-01', periods=100, freq='D')
    data = {
        'date': dates,
        'sunspots': [10] * 30 + [np.nan] * 10 + [20] * 30 + [np.nan] * 30  # Gap of 10 days, then gap of 30 days
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_gsn_large_gap():
    """Create a sample GSN DataFrame with a large gap (>1 year)."""
    dates = pd.date_range(start='2000-01-01', periods=100, freq='D')
    # Create a gap of 400 days (>= 1 year)
    data = {
        'date': dates,
        'sunspots': [10] * 20 + [np.nan] * 400 + [20] * 20  # Large gap
    }
    return pd.DataFrame(data)

def test_fill_gaps_linear_interpolation(sample_gsn_data):
    """Test that gaps < 1 year are filled via linear interpolation."""
    result = fill_gaps(sample_gsn_data)
    # Check that the gap of 10 days is filled
    assert not result['sunspots'].iloc[30:40].isna().all(), "Gap of 10 days should be interpolated."
    # Check that values are between the surrounding valid values (10 and 20)
    filled_values = result['sunspots'].iloc[30:40]
    assert all(10 <= v <= 20 for v in filled_values if not pd.isna(v)), "Interpolated values should be between 10 and 20."

def test_fill_gaps_large_gap(sample_gsn_large_gap):
    """Test that gaps >= 1 year are NOT filled (left as NaN) for TSI proxy handling."""
    result = fill_gaps(sample_gsn_large_gap)
    # The large gap should remain as NaN
    assert result['sunspots'].iloc[20:420].isna().all(), "Gap >= 1 year should remain as NaN."

def test_detect_cycle_boundaries():
    """Test cycle boundary detection."""
    dates = pd.date_range(start='2000-01-01', periods=1000, freq='D')
    data = {
        'date': dates,
        'cycle_id': [1] * 300 + [2] * 400 + [3] * 300
    }
    df = pd.DataFrame(data)
    boundaries = detect_cycle_boundaries(df)
    assert 1 in boundaries
    assert 2 in boundaries
    assert 3 in boundaries
    # Check approximate years (assuming daily data)
    assert boundaries[1][0] == 2000
    assert boundaries[1][1] == 2000  # 300 days is less than a year, so same year
    assert boundaries[2][1] == 2001  # 400 days spans into next year
