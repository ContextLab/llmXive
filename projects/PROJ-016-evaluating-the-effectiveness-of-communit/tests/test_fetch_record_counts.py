"""
Tests for T008: Fetch Record Counts.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure code directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.fetch_record_counts import (
    get_world_bank_countries_by_income,
    fetch_world_bank_records,
    fetch_fao_records,
    save_outputs
)

@pytest.fixture
def sample_countries():
    return ["USA", "CHN", "IND", "BRA"]

@patch('data.fetch_record_counts.requests.get')
def test_get_world_bank_countries_by_income(mock_get):
    """Test fetching low/middle income countries."""
    # Mock response structure: [metadata, [country1, country2, ...]]
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {}, # metadata
        [
            {"id": "USA", "incomeLevel": {"id": "HIC"}}, # High income - skip
            {"id": "BRA", "incomeLevel": {"id": "UMC"}}, # Upper middle - keep
            {"id": "IND", "incomeLevel": {"id": "LMC"}}, # Lower middle - keep
            {"id": "CHN", "incomeLevel": {"id": "UMC"}}  # Upper middle - keep
        ]
    ]
    mock_get.return_value = mock_response

    countries = get_world_bank_countries_by_income()
    
    assert "BRA" in countries
    assert "IND" in countries
    assert "CHN" in countries
    assert "USA" not in countries # High income
    assert mock_get.called

def test_save_outputs(tmp_path):
    """Test saving outputs to JSON."""
    output_file = tmp_path / "test_counts.json"
    
    save_outputs(
        wb_count=100,
        fao_count=50,
        output_path=output_file
    )
    
    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        data = json.load(f)
    
    assert data["total_records"] == 150
    assert data["world_bank"]["count"] == 100
    assert data["fao"]["count"] == 50
    assert data["year_range"] == (2000, 2020)

@patch('data.fetch_record_counts.requests.get')
def test_fetch_world_bank_records(mock_get, sample_countries):
    """Test fetching record counts from World Bank."""
    # Mock response for one country
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {},
        [
            {"year": 2000, "value": 10.5},
            {"year": 2001, "value": 10.6},
            {"year": 2002, "value": None} # Should be ignored
        ]
    ]
    mock_get.return_value = mock_response

    count = fetch_world_bank_records(sample_countries)
    
    # 3 countries * 2 valid records each = 6
    assert count == 6
    assert mock_get.call_count == len(sample_countries)

@patch('data.fetch_record_counts.requests.get')
def test_fetch_fao_records(mock_get, sample_countries):
    """Test fetching record counts from FAO."""
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {"Year": 2000, "Value": 100},
            {"Year": 2001, "Value": 101},
            {"Year": 2002, "Value": None}
        ]
    }
    mock_get.return_value = mock_response

    count = fetch_fao_records(sample_countries)
    
    # 3 countries * 2 valid records each = 6
    assert count == 6
    assert mock_get.call_count == len(sample_countries)