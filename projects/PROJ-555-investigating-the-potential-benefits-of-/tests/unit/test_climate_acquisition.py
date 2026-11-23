import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data_acquisition_climate import load_site_coordinates, fetch_nasa_power_climate_data, merge_climate_data

class TestClimateAcquisition:
    
    def test_load_site_coordinates_missing_file(self):
        """Test that load_site_coordinates raises FileNotFoundError if file is missing."""
        with patch("data_acquisition_climate.Path.exists", return_value=False):
            with pytest.raises(FileNotFoundError):
                load_site_coordinates()

    def test_merge_climate_data_empty(self):
        """Test merge_climate_data with empty lists."""
        with pytest.raises(ValueError):
            merge_climate_data([], [])

    def test_merge_climate_data_success(self):
        """Test merging precipitation and temperature data."""
        df_precip = pd.DataFrame([
            {"site_id": "A", "year": 2000, "month": 1, "precip_mm": 100.0}
        ])
        df_temp = pd.DataFrame([
            {"site_id": "A", "year": 2000, "month": 1, "temp_c": 25.0}
        ])
        
        result = merge_climate_data([df_precip], [df_temp])
        
        assert len(result) == 1
        assert "precip_mm" in result.columns
        assert "temp_c" in result.columns
        assert result.iloc[0]["precip_mm"] == 100.0
        assert result.iloc[0]["temp_c"] == 25.0

    @patch("data_acquisition_climate.requests.get")
    def test_fetch_nasa_power_success(self, mock_get):
        """Test successful fetch of NASA POWER data."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "properties": {
                "datetime": ["2000-01-01"],
                "parameter": {
                    "T2M": [25.5]
                }
            }
        }
        mock_get.return_value = mock_response

        df = fetch_nasa_power_climate_data("TEST", 0.0, 0.0, "2000-01-01", "2000-01-31")
        
        assert df is not None
        assert len(df) == 1
        assert df.iloc[0]["temp_c"] == 25.5

    @patch("data_acquisition_climate.requests.get")
    def test_fetch_nasa_power_failure(self, mock_get):
        """Test that fetch_nasa_power_climate_data raises RuntimeError on network failure."""
        mock_get.side_effect = Exception("Network Error")
        
        with pytest.raises(RuntimeError, match="Failed to fetch real NASA POWER data"):
            fetch_nasa_power_climate_data("TEST", 0.0, 0.0, "2000-01-01", "2000-01-31")
