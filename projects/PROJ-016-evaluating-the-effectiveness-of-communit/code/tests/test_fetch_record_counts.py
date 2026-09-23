import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd
import sys
import os

# Ensure code path is available
_CODE_PATH = Path(__file__).parent.parent
if str(_CODE_PATH) not in sys.path:
    sys.path.insert(0, str(_CODE_PATH))

from data.fetch_record_counts import fetch_world_bank_records, save_outputs, get_wb_stream_url

@pytest.fixture
def temp_data_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_wb_indicator_response():
    """Mock response for World Bank API indicating 2 pages of data."""
    page_1_meta = {"page": 1, "pages": 2, "per_page": 50000, "total": 100}
    page_1_data = [
        {"countryiso3code": "USA", "date": "2000", "value": 0.5},
        {"countryiso3code": "USA", "date": "2001", "value": 0.6},
        {"countryiso3code": "CAN", "date": "2000", "value": 0.4},
    ]
    
    page_2_meta = {"page": 2, "pages": 2, "per_page": 50000, "total": 100}
    page_2_data = [
        {"countryiso3code": "USA", "date": "2020", "value": 0.7},
    ]
    
    return [page_1_meta, page_1_data], [page_2_meta, page_2_data]

def test_get_world_bank_url():
    url, params = get_wb_stream_url("EG.GOV.POLI.ZS", 2000, 2020)
    assert "EG.GOV.POLI.ZS" in url
    assert params['date'] == '2000:2020'

@patch('data.fetch_record_counts.requests.get')
def test_fetch_world_bank_records(mock_get, mock_wb_indicator_response):
    """
    Verifies that the function correctly iterates pages and counts rows.
    """
    page_1, page_2 = mock_wb_indicator_response
    
    # Mock the response sequence
    mock_response_1 = MagicMock()
    mock_response_1.json.return_value = page_1
    mock_response_1.raise_for_status = MagicMock()
    
    mock_response_2 = MagicMock()
    mock_response_2.json.return_value = page_2
    mock_response_2.raise_for_status = MagicMock()
    
    mock_get.side_effect = [mock_response_1, mock_response_2]

    count = fetch_world_bank_records("EG.GOV.POLI.ZS", 2000, 2020)
    
    # Page 1 has 3 valid rows, Page 2 has 1 valid row
    expected_count = 4
    assert count == expected_count
    assert mock_get.call_count == 2

@patch('data.fetch_record_counts.requests.get')
def test_fetch_handles_api_error(mock_get):
    """Verifies that the function raises an error on persistent API failure."""
    mock_get.side_effect = Exception("Network Error")
    
    with pytest.raises(RuntimeError, match="Data fetch failed"):
        fetch_world_bank_records("EG.GOV.POLI.ZS", 2000, 2020)

def test_save_outputs(temp_data_dir):
    """Verifies that outputs are saved correctly to JSON."""
    output_path = temp_data_dir / "test_counts.json"
    save_outputs(150, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert data["total_wb_available"] == 150
    assert data["indicator"] == "EG.GOV.POLI.ZS"