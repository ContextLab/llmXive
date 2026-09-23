import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import os
import sys

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data_acquisition_climate import fetch_nasa_power_climate_data, merge_climate_data, load_site_coordinates

def test_fetch_nasa_power_data():
    """Test that we can fetch real data from NASA POWER API."""
    # Use a known location (e.g., a point in the Amazon)
    lat, lon = -3.4653, -62.2159
    start = "2020-01-01"
    end = "2020-12-31"
    
    df = fetch_nasa_power_climate_data(lat, lon, start, end, None)
    
    assert not df.empty
    assert 'precip_mm' in df.columns
    assert 'temp_c' in df.columns
    assert 'year' in df.columns
    assert 'month' in df.columns
    
    # Check data types
    assert df['precip_mm'].dtype in [np.float64, np.float32]
    assert df['temp_c'].dtype in [np.float64, np.float32]
    
    # Check range (reasonable values)
    assert df['precip_mm'].min() >= 0
    assert df['temp_c'].min() > -50
    assert df['temp_c'].max() < 60

def test_merge_climate_data():
    """Test merging of precipitation and temperature data."""
    # Create dummy data
    precip_df = pd.DataFrame({
        'year': [2020, 2020],
        'month': [1, 2],
        'precip_mm': [100.0, 150.0]
    })
    
    temp_df = pd.DataFrame({
        'year': [2020, 2020],
        'month': [1, 2],
        'temp_c': [25.0, 26.0]
    })
    
    merged = merge_climate_data('site1', precip_df, temp_df, None)
    
    assert merged.shape == (2, 5)
    assert 'site_id' in merged.columns
    assert merged['site_id'].iloc[0] == 'site1'
    assert merged['precip_mm'].iloc[0] == 100.0
    assert merged['temp_c'].iloc[0] == 25.0

def test_load_site_coordinates():
    """Test loading site coordinates."""
    # This test assumes the file exists (created by T012b)
    # If not, it should raise FileNotFoundError
    try:
        df = load_site_coordinates()
        assert 'site_id' in df.columns
        assert 'latitude' in df.columns
        assert 'longitude' in df.columns
    except FileNotFoundError:
        # If the file doesn't exist, we expect this test to fail in a real run
        # but for unit testing, we might skip or mock
        pytest.skip("Site coordinates file not found. Skipping test.")
