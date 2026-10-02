"""
Tests for T009: Fetch CBNRM Proxy functionality.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import pytest
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.fetch_cbmrm_proxy import validate_indicator_code, fetch_world_bank_indicator, save_outputs, main
import logging

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        (tmp_path / "data" / "raw").mkdir(parents=True, exist_ok=True)
        (tmp_path / "data" / "processed").mkdir(parents=True, exist_ok=True)
        yield tmp_path

@pytest.fixture
def mock_response_data():
    """Mock response data for World Bank API."""
    return [
        {
            "page": 1,
            "pages": 1,
            "perpage": 300,
            "total": 2,
            "sourceid": "",
            "sourcename": "",
            "lastupdated": ""
        },
        [
            {
                "countryiso3code": "USA",
                "date": "2020",
                "value": 10.5,
                "unit": "sq. km",
                "obs_status": "",
                "decimal": 1
            },
            {
                "countryiso3code": "USA",
                "date": "2019",
                "value": 10.4,
                "unit": "sq. km",
                "obs_status": "",
                "decimal": 1
            }
        ]
    ]

def test_validate_indicator_code(mock_response_data):
    """Test that validate_indicator_code returns True when indicator exists."""
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = validate_indicator_code("AG.LND.FRST.CF")
        assert result is True
        mock_get.assert_called_once()

def test_validate_indicator_code_no_data():
    """Test that validate_indicator_code returns False when indicator is missing."""
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        # Empty list of indicators
        mock_response.json.return_value = [{"page": 1, "pages": 1}, []]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = validate_indicator_code("NON.EXISTENT.IND")
        assert result is False

def test_fetch_world_bank_indicator_success(mock_response_data, temp_data_dir):
    """Test successful fetch of World Bank indicator."""
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = fetch_world_bank_indicator("AG.LND.FRST.CF", 2000, 2020)
        
        assert result is not None
        assert result["indicator"] == "AG.LND.FRST.CF"
        assert len(result["data"]) == 2
        assert result["data"][0]["countryiso3code"] == "USA"

def test_save_outputs(temp_data_dir, mock_response_data):
    """Test that save_outputs creates correct files."""
    # Prepare mock data
    fetched_data = {
        "indicator": "AG.LND.FRST.CF",
        "data": mock_response_data[1]
    }
    
    csv_path = temp_data_dir / "data" / "raw" / "cbnrm_proxy.csv"
    json_path = temp_data_dir / "data" / "processed" / "cbnrm_proxy_metadata.json"
    
    success = save_outputs(fetched_data, csv_path, json_path)
    
    assert success is True
    assert csv_path.exists()
    assert json_path.exists()
    
    # Verify CSV content
    df = pd.read_csv(csv_path)
    assert len(df) == 2
    assert "USA" in df["countryiso3code"].values
    
    # Verify JSON content
    with open(json_path) as f:
        metadata = json.load(f)
    assert metadata["status"] == "success"
    assert metadata["indicator"] == "AG.LND.FRST.CF"

def test_main_halt_on_failure():
    """Test that main() exits with code 1 when indicator is missing."""
    with patch('requests.get') as mock_get:
        # Simulate missing indicator
        mock_response = MagicMock()
        mock_response.json.return_value = [{"page": 1}, []]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with patch('sys.exit') as mock_exit:
            main()
            mock_exit.assert_called_once_with(1)