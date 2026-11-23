"""
Unit tests for ERA5 ingestion logic.
"""
import pytest
import pandas as pd
from pathlib import Path
import sys
import os

from src.data.ingest import validate_era5_data, fetch_era5_data

@pytest.fixture
def valid_era5_df():
    """Create a valid sample ERA5 DataFrame."""
    data = {
        'date': ['2023-01-01', '2023-01-01', '2023-01-02'],
        'level': [1000, 500, 1000],
        'value': [280.5, 260.2, 281.0],
        'latitude': [0, 0, 0],
        'longitude': [0, 0, 0]
    }
    return pd.DataFrame(data)

def test_validate_era5_data_valid(valid_era5_df):
    """Test validation with valid data."""
    assert validate_era5_data(valid_era5_df) is True

def test_validate_era5_data_missing_columns(valid_era5_df):
    """Test validation with missing required columns."""
    df = valid_era5_df.drop(columns=['level'])
    assert validate_era5_data(df) is False

def test_validate_era5_data_null_values(valid_era5_df):
    """Test validation with null values."""
    df = valid_era5_df.copy()
    df.loc[0, 'date'] = None
    assert validate_era5_data(df) is False

def test_validate_era5_data_out_of_range_pressure(valid_era5_df):
    """Test validation with out-of-range pressure levels (warning only, returns True)."""
    df = valid_era5_df.copy()
    df.loc[0, 'level'] = 5000 # Invalid level
    # The function currently logs a warning but returns True
    # If strict validation is required, change the logic in ingest.py
    assert validate_era5_data(df) is True 
