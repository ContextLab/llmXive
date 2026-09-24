"""
Unit tests for T008b: Count World Bank Rows
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.fetch_wb_record_counts import (
    fetch_world_bank_indicator_count,
    count_world_bank_rows,
    save_outputs
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@patch('data.fetch_wb_record_counts.requests.get')
def test_fetch_world_bank_indicator_count_success(mock_get):
    """Test successful fetching of indicator count."""
    # Mock response structure
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"page": 1, "pages": 1, "perpage": 5000, "total": 2},
        [
            {"country": {"id": "USA", "value": "USA"}, "indicator": {"id": "EG.GOV.POLI.ZS", "value": "Political Stability"}, "countryiso3code": "USA", "date": "2000", "value": 0.5, "unit": "", "obs_status": "", "decimal": 1},
            {"country": {"id": "USA", "value": "USA"}, "indicator": {"id": "EG.GOV.POLI.ZS", "value": "Political Stability"}, "countryiso3code": "USA", "date": "2001", "value": 0.6, "unit": "", "obs_status": "", "decimal": 1}
        ]
    ]
    mock_get.return_value = mock_response

    count = fetch_world_bank_indicator_count("EG.GOV.POLI.ZS", 2000, 2001)
    
    assert count == 2
    mock_get.assert_called_once()

@patch('data.fetch_wb_record_counts.requests.get')
def test_fetch_world_bank_indicator_count_pagination(mock_get):
    """Test fetching with multiple pages."""
    # Mock first page
    mock_response1 = MagicMock()
    mock_response1.status_code = 200
    mock_response1.json.return_value = [
        {"page": 1, "pages": 2, "perpage": 2, "total": 4},
        [
            {"country": {"id": "USA", "value": "USA"}, "indicator": {"id": "EG.GOV.POLI.ZS", "value": "Political Stability"}, "countryiso3code": "USA", "date": "2000", "value": 0.5, "unit": "", "obs_status": "", "decimal": 1},
            {"country": {"id": "USA", "value": "USA"}, "indicator": {"id": "EG.GOV.POLI.ZS", "value": "Political Stability"}, "countryiso3code": "USA", "date": "2001", "value": 0.6, "unit": "", "obs_status": "", "decimal": 1}
        ]
    ]
    
    # Mock second page
    mock_response2 = MagicMock()
    mock_response2.status_code = 200
    mock_response2.json.return_value = [
        {"page": 2, "pages": 2, "perpage": 2, "total": 4},
        [
            {"country": {"id": "USA", "value": "USA"}, "indicator": {"id": "EG.GOV.POLI.ZS", "value": "Political Stability"}, "countryiso3code": "USA", "date": "2002", "value": 0.7, "unit": "", "obs_status": "", "decimal": 1},
            {"country": {"id": "USA", "value": "USA"}, "indicator": {"id": "EG.GOV.POLI.ZS", "value": "Political Stability"}, "countryiso3code": "USA", "date": "2003", "value": 0.8, "unit": "", "obs_status": "", "decimal": 1}
        ]
    ]
    
    mock_get.side_effect = [mock_response1, mock_response2]

    count = fetch_world_bank_indicator_count("EG.GOV.POLI.ZS", 2000, 2003)
    
    assert count == 4
    assert mock_get.call_count == 2

def test_save_outputs(temp_data_dir):
    """Test saving outputs to JSON file."""
    counts = {
        "cbnrm_proxy_count": 100,
        "gdp_count": 100,
        "population_count": 100,
        "total_wb_available": 100,
        "year_range": "2000-2020",
        "indicators": {
            "cbnrm_proxy": "EG.GOV.POLI.ZS",
            "gdp": "NY.GDP.PCAP.CD",
            "population": "SP.POP.TOTL"
        }
    }
    
    output_path = temp_data_dir / "counts_wb.json"
    save_outputs(counts, output_path)
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        saved_data = json.load(f)
    
    assert saved_data["total_wb_available"] == 100
    assert saved_data["year_range"] == "2000-2020"

@patch('data.fetch_wb_record_counts.fetch_world_bank_indicator_count')
def test_count_world_bank_rows(mock_fetch_count):
    """Test the main counting function."""
    mock_fetch_count.side_effect = [100, 100, 100]  # cbnrm, gdp, pop
    
    result = count_world_bank_rows()
    
    assert result["total_wb_available"] == 100
    assert result["cbnrm_proxy_count"] == 100
    assert result["gdp_count"] == 100
    assert result["population_count"] == 100
    assert "year_range" in result
    assert "indicators" in result