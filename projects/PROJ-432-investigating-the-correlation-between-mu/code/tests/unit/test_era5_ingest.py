import pytest
import pandas as pd
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.data.ingest import validate_era5_data, fetch_era5_data

@pytest.fixture
def valid_era5_df():
    """Create a mock valid ERA5 DataFrame."""
    data = {
        'date': pd.date_range('2023-01-01', periods=5, freq='D'),
        'pressure_level': [1000.0, 850.0, 700.0, 500.0, 200.0] * 5,
        'temperature': [-20.0, -10.0, -20.0, -30.0, -50.0] * 5
    }
    # Repeat dates to match pressure levels
    dates = []
    for d in data['date']:
        dates.extend([d] * 5)
    data['date'] = dates
    return pd.DataFrame(data)

def test_validate_era5_data_valid(valid_era5_df):
    """Test validation with valid data."""
    assert validate_era5_data(valid_era5_df) is True

def test_validate_era5_data_missing_columns():
    """Test validation with missing columns."""
    df = pd.DataFrame({'date': [1], 'pressure_level': [1]})
    assert validate_era5_data(df) is False

def test_validate_era5_data_null_values():
    """Test validation with null values."""
    df = pd.DataFrame({
        'date': [1, 2],
        'pressure_level': [100.0, None],
        'temperature': [20.0, 20.0]
    })
    assert validate_era5_data(df) is False

def test_validate_era5_data_out_of_range_pressure():
    """Test validation with pressure levels out of range."""
    df = pd.DataFrame({
        'date': [1, 2],
        'pressure_level': [10.0, 1001.0],
        'temperature': [20.0, 20.0]
    })
    assert validate_era5_data(df) is False

# Note: We do not test fetch_era5_data directly here because it requires
# a real CDS API key and network access. Integration tests should handle that.
# The unit tests focus on the validation logic which is deterministic.