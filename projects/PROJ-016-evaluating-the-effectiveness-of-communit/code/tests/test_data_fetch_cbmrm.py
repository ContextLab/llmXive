import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import pytest

import sys
import os
# Ensure code is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.fetch_cbmrm_proxy import fetch_world_bank_indicator, validate_indicator_code, save_outputs, CBNRM_INDICATOR_CODE

@pytest.fixture
def mock_response_data():
    return [
        {"page": 1, "pages": 1, "per_page": 10000, "total": 2},
        [
            {
                "country": {"id": "USA", "value": "United States"},
                "countryiso3code": "USA",
                "date": "2000",
                "value": 33.5,
                "unit": "",
                "obs_status": "",
                "decimal": 1
            },
            {
                "country": {"id": "USA", "value": "United States"},
                "countryiso3code": "USA",
                "date": "2001",
                "value": 33.6,
                "unit": "",
                "obs_status": "",
                "decimal": 1
            },
            {
                "country": {"id": "BRA", "value": "Brazil"},
                "countryiso3code": "BRA",
                "date": "2000",
                "value": 60.0,
                "unit": "",
                "obs_status": "",
                "decimal": 1
            }
        ]
    ]

@patch('data.fetch_cbmrm_proxy.requests.get')
def test_fetch_world_bank_indicator_success(mock_get, mock_response_data):
    mock_response = MagicMock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = fetch_world_bank_indicator("TEST_IND", 2000, 2001)

    assert len(result) == 3
    assert result[0]["countryiso3code"] == "USA"
    assert result[0]["value"] == 33.5
    mock_get.assert_called_once()

@patch('data.fetch_cbmrm_proxy.requests.get')
def test_fetch_world_bank_indicator_retry(mock_get):
    # First call fails, second succeeds
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {"page": 1, "pages": 1, "per_page": 100, "total": 1},
        [{"country": "USA", "countryiso3code": "USA", "date": "2000", "value": 10.0}]
    ]
    mock_response.raise_for_status.return_value = None

    # Configure side effect: raise error first, then success
    mock_get.side_effect = [
        Exception("Connection Error"),
        mock_response
    ]

    result = fetch_world_bank_indicator("TEST_IND", 2000, 2000)

    assert len(result) == 1
    assert mock_get.call_count == 2

@patch('data.fetch_cbmrm_proxy.fetch_world_bank_indicator')
def test_validate_indicator_code(mock_fetch):
    mock_fetch.return_value = [
        {"countryiso3code": "USA", "date": "2000", "value": 10.0}
    ]

    assert validate_indicator_code("TEST_IND") is True
    mock_fetch.assert_called_once()

@patch('data.fetch_cbmrm_proxy.fetch_world_bank_indicator')
def test_validate_indicator_code_no_data(mock_fetch):
    mock_fetch.return_value = []
    assert validate_indicator_code("TEST_IND") is False

def test_save_outputs(tmp_path):
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    raw_dir.mkdir()
    processed_dir.mkdir()

    data = [
        {"countryiso3code": "USA", "country": {"value": "USA"}, "date": "2000", "value": 10.0},
        {"countryiso3code": "USA", "country": {"value": "USA"}, "date": "2001", "value": 11.0},
        {"countryiso3code": "BRA", "country": {"value": "Brazil"}, "date": "2000", "value": 20.0}
    ]

    save_outputs(data, "TEST_CODE", "http://example.com", raw_dir, processed_dir)

    # Check CSV
    csv_path = raw_dir / "cbnrm_proxy.csv"
    assert csv_path.exists()
    df = pd.read_csv(csv_path)
    assert len(df) == 3
    assert "USA" in df["country_iso3"].values
    assert "BRA" in df["country_iso3"].values

    # Check JSON
    json_path = processed_dir / "cbnrm_proxy_metadata.json"
    assert json_path.exists()
    with open(json_path) as f:
        meta = json.load(f)
    assert meta["indicator_code"] == "TEST_CODE"
    assert meta["total_records"] == 3
