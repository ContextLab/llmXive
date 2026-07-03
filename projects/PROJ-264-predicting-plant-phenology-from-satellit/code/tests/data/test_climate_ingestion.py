"""
Tests for climate data ingestion functionality.
"""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.ingestion import (
    fetch_nasa_power_climate,
    align_climate_with_satellite,
    run_climate_ingestion
)
from src.config import get_config

@pytest.fixture
def mock_power_response():
    """Mock response from NASA POWER API."""
    return {
        "properties": {
            "daily": {
                "2023-01-01": {
                    "T2M_MAX": 280.15,
                    "T2M_MIN": 275.15,
                    "PRECTOT": 0.0,
                    "SOLAR": 15000.0
                },
                "2023-01-02": {
                    "T2M_MAX": 282.15,
                    "T2M_MIN": 276.15,
                    "PRECTOT": 2.5,
                    "SOLAR": 16000.0
                },
                "2023-01-03": {
                    "T2M_MAX": 281.15,
                    "T2M_MIN": 277.15,
                    "PRECTOT": 0.0,
                    "SOLAR": 15500.0
                }
            }
        }
    }

@patch('src.data.ingestion.requests.get')
def test_fetch_nasa_power_climate(mock_get, mock_power_response):
    """Test fetching climate data from NASA POWER API."""
    mock_response = MagicMock()
    mock_response.json.return_value = mock_power_response
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    result = fetch_nasa_power_climate(
        lat=40.0,
        lon=-105.0,
        start_date="2023-01-01",
        end_date="2023-01-03"
    )

    assert result is not None
    assert len(result) == 3
    assert "temp_max" in result.columns
    assert "temp_min" in result.columns
    assert "temp_mean" in result.columns
    assert "precip" in result.columns
    assert "solar_rad" in result.columns

    # Check temperature conversion (Kelvin to Celsius)
    assert result.loc[pd.Timestamp("2023-01-01"), "temp_max"] == 7.0  # 280.15 - 273.15
    assert result.loc[pd.Timestamp("2023-01-01"), "temp_min"] == 2.0  # 275.15 - 273.15

def test_align_climate_with_satellite():
    """Test alignment of climate data with satellite timestamps."""
    # Create sample climate data
    climate_data = {
        "2023-01-01": {"temp_mean": 5.0, "precip": 0.0},
        "2023-01-02": {"temp_mean": 6.0, "precip": 2.0},
        "2023-01-03": {"temp_mean": 5.5, "precip": 0.0}
    }
    climate_df = pd.DataFrame(climate_data).T
    climate_df.index = pd.to_datetime(climate_df.index)

    # Create sample satellite data
    satellite_data = {
        "2023-01-01": {"ndvi": 0.3},
        "2023-01-05": {"ndvi": 0.4}  # Gap of 4 days
    }
    satellite_df = pd.DataFrame(satellite_data).T
    satellite_df.index = pd.to_datetime(satellite_df.index)

    # Align with tolerance of 3 days
    aligned_df = align_climate_with_satellite(climate_df, satellite_df, tolerance_days=3)

    # First date should align exactly
    assert pd.Timestamp("2023-01-01") in aligned_df.index

    # Second date (2023-01-05) should not align (gap > 3 days)
    # It will have NaN for climate columns
    assert pd.Timestamp("2023-01-05") in aligned_df.index
    assert pd.isna(aligned_df.loc[pd.Timestamp("2023-01-05"), "temp_mean"])

@patch('src.data.ingestion.fetch_nasa_power_climate')
def test_run_climate_ingestion(mock_fetch):
    """Test the main climate ingestion function."""
    # Mock the fetch function to return sample data
    sample_df = pd.DataFrame({
        "temp_max": [10.0, 12.0, 8.0],
        "temp_min": [2.0, 4.0, 0.0],
        "precip": [0.0, 5.0, 0.0],
        "solar_rad": [15000.0, 16000.0, 14000.0]
    }, index=pd.date_range("2023-01-01", periods=3, freq="D"))
    sample_df["site_id"] = "test_site_1"

    mock_fetch.return_value = sample_df

    # Mock config
    with patch('src.data.ingestion.get_config') as mock_config:
        mock_config.return_value = {
            "study_sites": [
                {"site_id": "test_site_1", "latitude": 40.0, "longitude": -105.0}
            ],
            "climate_start_date": "2023-01-01",
            "climate_end_date": "2023-01-03",
            "data_processed_dir": "data/processed"
        }

        result = run_climate_ingestion()

        assert result is not None
        assert len(result) == 3
        assert "site_id" in result.columns
        assert result["site_id"].iloc[0] == "test_site_1"
        assert "temp_mean" in result.columns