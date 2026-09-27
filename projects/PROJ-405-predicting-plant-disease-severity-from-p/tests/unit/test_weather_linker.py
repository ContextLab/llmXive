"""
Unit tests for code/weather_linker.py
Verifies 7-day aggregation and date arithmetic logic.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from weather_linker import get_weather_for_record, fetch_historical_weather

def test_get_weather_for_record_missing_location(caplog):
    """Test that records with missing location are handled correctly."""
    record = {
        "image_path": "test.jpg",
        "location_lat": None,
        "location_lon": None,
        "image_date": "2023-01-01"
    }
    
    with patch("weather_linker.fetch_historical_weather") as mock_fetch:
        result = get_weather_for_record(record)
        # Should return None or a specific failure indicator
        assert result is None
        assert "Missing location" in caplog.text or "excluded" in caplog.text.lower()

def test_fetch_historical_weather_structure():
    """Test that the weather fetcher returns the expected structure (mocked)."""
    lat, lon = 40.7128, -74.0060
    date_start = datetime(2023, 1, 1)
    date_end = datetime(2023, 1, 8)
    
    mock_response = {
        "daily": {
            "time": ["2023-01-01", "2023-01-02"],
            "temperature_2m_mean": [10.0, 12.0],
            "relative_humidity_2m_mean": [60.0, 65.0],
            "precipitation_sum": [0.0, 5.0]
        }
    }
    
    with patch("weather_linker.requests.get") as mock_get:
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.raise_for_status = MagicMock()
        
        result = fetch_historical_weather(lat, lon, date_start, date_end)
        
        assert result is not None
        assert "mean_temp" in result
        assert "mean_humidity" in result
        assert "total_precipitation" in result
        # Check aggregation logic (mean of 2 days)
        assert result["mean_temp"] == 11.0
        assert result["total_precipitation"] == 5.0
