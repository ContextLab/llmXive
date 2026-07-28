"""
Unit tests for climate data acquisition module.
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data_acquisition_climate import (
    load_site_coordinates,
    fetch_nasa_power_temperature,
    merge_climate_data,
    main
)

def test_load_site_coordinates_missing_file(tmp_path):
    """Test that load_site_coordinates raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        load_site_coordinates(str(tmp_path / "nonexistent.csv"))

def test_merge_climate_data():
    """Test merging of precipitation and temperature data."""
    # Create mock data
    chirps_df = pd.DataFrame({
        "date": pd.date_range("2020-01-01", periods=3, freq="MS"),
        "precipitation_mm": [10.0, 20.0, 30.0]
    })
    
    power_df = pd.DataFrame({
        "date": pd.date_range("2020-01-01", periods=3, freq="MS"),
        "temperature_c": [15.0, 16.0, 17.0]
    })
    
    merged = merge_climate_data(chirps_df, power_df, "test_site")
    
    assert "precipitation_mm" in merged.columns
    assert "temperature_c" in merged.columns
    assert "site_id" in merged.columns
    assert merged["site_id"].iloc[0] == "test_site"
    assert len(merged) == 3

@patch("data_acquisition_climate.requests.post")
def test_fetch_nasa_power_temperature_success(mock_post):
    """Test successful fetch from NASA POWER API."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "properties": {
            "parameter": {
                "T2M": {
                    "2020-01-01": 15.0,
                    "2020-02-01": 16.0
                }
            }
        }
    }
    mock_post.return_value = mock_response
    
    df = fetch_nasa_power_temperature(0.0, 0.0, 2020, 2020)
    
    assert not df.empty
    assert "temperature_c" in df.columns
    assert len(df) == 2

@patch("data_acquisition_climate.requests.post")
def test_fetch_nasa_power_temperature_failure(mock_post):
    """Test that fetch raises error on API failure."""
    mock_post.side_effect = Exception("API Error")
    
    with pytest.raises(RuntimeError):
        fetch_nasa_power_temperature(0.0, 0.0, 2020, 2020)

def test_main_fails_without_site_coordinates(tmp_path):
    """Test that main fails if site_coordinates.csv is missing."""
    # Create a temp directory structure
    data_dir = tmp_path / "data" / "raw"
    data_dir.mkdir(parents=True)
    
    # Do not create site_coordinates.csv
    
    with patch("data_acquisition_climate.Path", return_value=tmp_path):
        with pytest.raises(SystemExit):
            main()