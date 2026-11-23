import pytest
import pandas as pd
from pathlib import Path
import sys
import os
from src.data.ingest import validate_era5_data, fetch_era5_data

@pytest.fixture
def valid_era5_df():
    """Create a valid sample DataFrame for ERA5 data."""
    data = {
        'date': pd.date_range('2023-01-01', periods=3),
        'pressure_level': [1000, 500, 100] * 3,
        'variable': ['temperature', 'temperature', 'temperature'] * 3,
        'value': [270.0, 250.0, 220.0] * 3
    }
    return pd.DataFrame(data)

def test_validate_era5_data_valid(valid_era5_df):
    """Test that a valid DataFrame passes validation."""
    assert validate_era5_data(valid_era5_df) is True

def test_validate_era5_data_missing_columns(valid_era5_df):
    """Test that a DataFrame with missing columns raises ValueError."""
    df = valid_era5_df.drop(columns=['variable'])
    with pytest.raises(ValueError, match="Missing required column"):
        validate_era5_data(df)

def test_validate_era5_data_null_values(valid_era5_df):
    """Test that a DataFrame with null values raises ValueError."""
    df = valid_era5_df.copy()
    df.loc[0, 'value'] = None
    with pytest.raises(ValueError, match="Null values found"):
        validate_era5_data(df)

def test_validate_era5_data_out_of_range_pressure(valid_era5_df):
    """Test that a DataFrame with invalid pressure levels raises ValueError."""
    df = valid_era5_df.copy()
    df.loc[0, 'pressure_level'] = 9999 # Invalid level
    with pytest.raises(ValueError, match="Invalid pressure levels found"):
        validate_era5_data(df)

# Note: We do not test fetch_era5_data with real API calls in unit tests
# as it requires credentials and network access. Integration tests handle that.