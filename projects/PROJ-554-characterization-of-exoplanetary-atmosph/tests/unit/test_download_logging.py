import pytest
import logging
from unittest.mock import patch, MagicMock
from pathlib import Path
import json

from download import fetch_spectrum_data, parse_spectrum_metadata, process_download_metadata
from utils import DataFetchError

@pytest.fixture
def mock_response():
    """Mock a valid API response."""
    data = {
        "data": [
            {
                "pl_name": "HD 209458 b",
                "pl_eqt": 1450.0,
                "pl_met": 0.02,
                "resolution": 100.0,
                "snr": 50.0,
                "pl_orbper": 3.52
            }
        ]
    }
    mock = MagicMock()
    mock.json.return_value = data
    mock.status_code = 200
    mock.headers = {'Content-Type': 'application/json'}
    return mock

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for output."""
    return tmp_path

@patch('download.requests.get')
def test_fetch_spectrum_data_logs_success(mock_get, mock_response, temp_dir, caplog):
    """Test that fetch_spectrum_data logs success and saves file."""
    mock_get.return_value = mock_response
    planet = "HD 209458 b"
    
    with caplog.at_level(logging.INFO):
        path, meta = fetch_spectrum_data(planet, temp_dir)
    
    assert path is not None
    assert path.exists()
    assert f"Fetching data for planet: {planet}" in caplog.text
    assert f"Successfully retrieved metadata for {planet}" in caplog.text
    assert f"Raw spectrum data saved to:" in caplog.text

@patch('download.requests.get')
def test_fetch_spectrum_data_logs_timeout(mock_get, temp_dir, caplog):
    """Test that fetch_spectrum_data logs timeout error."""
    import requests
    mock_get.side_effect = requests.exceptions.Timeout()
    planet = "HD 209458 b"
    
    with pytest.raises(DataFetchError):
        with caplog.at_level(logging.ERROR):
            fetch_spectrum_data(planet, temp_dir)
    
    assert f"Timeout fetching data for {planet}" in caplog.text

@patch('download.requests.get')
def test_process_download_metadata_progress_logging(mock_get, temp_dir, caplog):
    """Test that process_download_metadata logs progress for each planet."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": [{"pl_name": "P1", "pl_eqt": 1000, "pl_met": 0.1, "resolution": 50, "snr": 10}]
    }
    mock_response.status_code = 200
    mock_response.headers = {}
    
    mock_get.return_value = mock_response
    
    planets = ["P1", "P2"]
    
    # Mock the second planet to return no data
    def side_effect(url, params, **kwargs):
        if params.get('cmd') and 'P2' in params.get('cmd'):
            m = MagicMock()
            m.json.return_value = {"data": []}
            m.status_code = 200
            return m
        return mock_response

    mock_get.side_effect = side_effect

    with caplog.at_level(logging.INFO):
        result = process_download_metadata(planets, temp_dir)
    
    assert len(result) == 1
    assert f"Processing P1" in caplog.text
    assert f"Processing P2" in caplog.text
    assert f"Success: P1" in caplog.text
    assert f"No data returned for P2" in caplog.text
    assert "Batch download complete" in caplog.text

def test_parse_spectrum_metadata_logs_parsing(caplog):
    """Test that parse_spectrum_metadata logs parsed values."""
    raw_meta = {
        "pl_name": "Test b",
        "pl_eqt": 1200.5,
        "pl_met": -0.5,
        "resolution": 200,
        "snr": 30
    }
    
    with caplog.at_level(logging.DEBUG):
        parsed = parse_spectrum_metadata(raw_meta, "Test b")
    
    assert parsed['equilibrium_temperature'] == 1200.5
    assert "Parsed equilibrium_temperature for Test b" in caplog.text
    assert "Metadata parsed for Test b" in caplog.text