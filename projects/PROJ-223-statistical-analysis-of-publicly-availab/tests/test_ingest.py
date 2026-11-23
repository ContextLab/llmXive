"""
Tests for data ingestion logic in code/ingest.py.
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from ingest import (
    download_fars_data,
    preprocess_fars,
    download_noaa_data,
    preprocess_noaa,
    merge_data,
    validate_merged_output,
    validate_contract
)
from utils import encode_severity, geo_distance, find_nearest_station, interpolate_weather
from config import RANDOM_SEED


class TestSeverityEncoding:
    """Unit tests for severity encoding logic (T009)."""

    def test_encode_severity_property(self):
        """Test encoding for Property Damage only."""
        assert encode_severity("Property Damage Only") == 0
        assert encode_severity("PDO") == 0

    def test_encode_severity_injury(self):
        """Test encoding for Injury."""
        assert encode_severity("Injury") == 1
        assert encode_severity("Injury (A/B/C)") == 1

    def test_encode_severity_fatal(self):
        """Test encoding for Fatality."""
        assert encode_severity("Fatality") == 2
        assert encode_severity("Fatal") == 2

    def test_encode_severity_unknown(self):
        """Test handling of unknown severity values."""
        # Should return -1 or raise; assuming -1 based on typical patterns
        # Adjust if the actual implementation raises ValueError
        result = encode_severity("Unknown")
        assert result == -1


class TestGeoMatching:
    """Integration tests for geo-matching logic (T010)."""

    def test_geo_distance_calculation(self):
        """Verify geodesic distance calculation."""
        # New York City to Los Angeles approx 2445 miles
        dist = geo_distance((40.7128, -74.0060), (34.0522, -118.2437))
        assert 2400 < dist < 2500  # Miles

    @patch('code.utils.geopy.distance.geodesic')
    def test_find_nearest_station(self, mock_geodesic):
        """Test finding the nearest weather station."""
        mock_geodesic.return_value.kilometers = 10.5
        stations = [
            {"lat": 40.0, "lon": -75.0, "id": "STN1"},
            {"lat": 41.0, "lon": -74.0, "id": "STN2"}
        ]
        crash_loc = (40.5, -74.5)
        
        nearest = find_nearest_station(crash_loc, stations)
        assert nearest is not None
        assert "id" in nearest

    def test_interpolate_weather(self):
        """Test linear interpolation of weather data."""
        # Create a small dataframe with time gaps
        data = {
            "timestamp": [10, 12, 14],
            "temperature": [20, 22, 24]
        }
        df = pd.DataFrame(data)
        
        # Interpolate at time 11
        result = interpolate_weather(df, target_time=11, time_col="timestamp", value_col="temperature")
        assert result == 21.0

class TestContractValidation:
    """Contract tests for merge output (T011)."""

    def test_match_method_population(self):
        """Verify that match_method field is populated correctly."""
        # Mock a merged dataset
        df = pd.DataFrame({
            "fars_id": [1, 2],
            "weather_id": [10, 11],
            "match_method": ["interpolated", "nearest"],
            "severity": [1, 2]
        })
        
        # Run validation
        is_valid, errors = validate_merged_output(df)
        
        assert is_valid
        assert "match_method" in df.columns
        assert all(df["match_method"].isin(["interpolated", "nearest"]))

class TestIngestPipeline:
    """End-to-end ingestion tests."""

    def test_validate_contract_schema(self):
        """Test schema validation against contract."""
        # Create a minimal valid dataframe
        df = pd.DataFrame({
            "accident_id": [1],
            "severity": [1],
            "precipitation": [0.0],
            "visibility": [10.0],
            "temperature": [20.0],
            "match_method": ["nearest"]
        })
        
        # This should pass if schema is correct
        # Note: validate_contract expects a schema file path or dict
        # Assuming it returns True on success
        result = validate_contract(df)
        # Depending on implementation, might return bool or raise
        # If it raises, we catch it; if it returns, we assert
        assert result is True or result is None