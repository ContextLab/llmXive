"""
Tests for the data ingestion module (T008).
"""

import pytest
import json
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

from code.data_ingestion import (
    fetch_solar_irradiance,
    process_irradiance_data,
    save_irradiance_profile,
    get_sub_saharan_africa_profile,
    DEFAULT_AVG_IRRADIANCE
)
from utils import get_project_root, get_data_dir
from code.config import get_config

# Mock API Response Data
MOCK_RAW_RESPONSE = {
    "properties": {
        "date": ["20230101", "20230102", "20230103"],
        "parameter": {
            "ALLSKY_SWH_DY": [5.2, None, 0.0] # Valid, Missing, Zero
        }
    }
}

def test_fetch_solar_irradiance_valid_params():
    """Test that fetch_solar_irradiance constructs the correct request."""
    with patch('code.data_ingestion.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {"properties": {"date": []}}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        fetch_solar_irradiance(1.0, 2.0, "20230101", "20230102")

        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[1]['params']['latitude'] == 1.0
        assert call_args[1]['params']['longitude'] == 2.0
        assert call_args[1]['params']['start'] == "20230101"
        assert call_args[1]['params']['end'] == "20230102"

def test_fetch_solar_irradiance_invalid_latitude():
    """Test that fetch_solar_irradiance raises ProjectError for invalid latitude."""
    with pytest.raises(Exception) as exc_info:
        fetch_solar_irradiance(100.0, 1.0, "20230101", "20230102")
    assert "Invalid latitude" in str(exc_info.value)

def test_fetch_solar_irradiance_invalid_longitude():
    """Test that fetch_solar_irradiance raises ProjectError for invalid longitude."""
    with pytest.raises(Exception) as exc_info:
        fetch_solar_irradiance(1.0, 200.0, "20230101", "20230102")
    assert "Invalid longitude" in str(exc_info.value)

def test_process_irradiance_data_handles_missing_and_zero():
    """Test that process_irradiance_data replaces None and 0 with DEFAULT_AVG_IRRADIANCE."""
    result = process_irradiance_data(MOCK_RAW_RESPONSE, "TestRegion")

    assert len(result) == 3
    assert result[0]['irradiance'] == 5.2 # Valid
    assert result[1]['irradiance'] == DEFAULT_AVG_IRRADIANCE # Missing (None)
    assert result[2]['irradiance'] == DEFAULT_AVG_IRRADIANCE # Zero

def test_process_irradiance_data_invalid_structure():
    """Test that process_irradiance_data raises ProjectError for invalid structure."""
    with pytest.raises(Exception) as exc_info:
        process_irradiance_data({"wrong_key": {}})
    assert "Invalid raw data structure" in str(exc_info.value)

def test_save_irradiance_profile_creates_file():
    """Test that save_irradiance_profile creates a JSON file."""
    test_records = [{"date": "20230101", "irradiance": 5.0}]
    filename = "test_profile.json"
    
    # Ensure the directory exists for the test
    data_dir = get_data_dir()
    raw_dir = data_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    try:
        path = save_irradiance_profile(test_records, filename)
        
        assert path.exists()
        with open(path, 'r') as f:
            loaded = json.load(f)
        assert loaded == test_records
    finally:
        # Cleanup
        if path.exists():
            path.unlink()

def test_get_sub_saharan_africa_profile_integration():
    """
    Integration test: Mock the API call and verify the full pipeline
    fetches, processes, and returns data with fallback logic applied.
    """
    mock_response_data = {
        "properties": {
            "date": ["20230601", "20230602", "20230603"],
            "parameter": {
                "ALLSKY_SWH_DY": [6.0, None, -1.0] # Valid, Missing, Negative
            }
        }
    }

    with patch('code.data_ingestion.fetch_solar_irradiance') as mock_fetch:
        mock_fetch.return_value = mock_response_data
        
        result = get_sub_saharan_africa_profile("20230601", "20230603")
        
        assert len(result) == 3
        assert result[0]['irradiance'] == 6.0
        assert result[1]['irradiance'] == DEFAULT_AVG_IRRADIANCE # None -> Avg
        assert result[2]['irradiance'] == DEFAULT_AVG_IRRADIANCE # Negative -> Avg
        # Verify the location used (Nairobi)
        mock_fetch.assert_called_once()
        call_kwargs = mock_fetch.call_args.kwargs
        assert abs(call_kwargs['latitude'] - (-1.2921)) < 0.001
        assert abs(call_kwargs['longitude'] - 36.8219) < 0.001