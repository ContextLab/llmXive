"""
Tests for fetch_record_counts module.

These tests verify the logic for fetching and counting records from
FAO and World Bank APIs.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from data.fetch_record_counts import (
    get_world_bank_countries_by_income,
    fetch_world_bank_records,
    fetch_fao_records,
    save_outputs,
    main
)

@pytest.fixture
def mock_wb_countries_response():
    """Mock response for World Bank countries API."""
    return {
        "page": 1,
        "pages": 1,
        "per_page": 3000,
        "total": 3,
        "country": [
            {
                "id": "AFG",
                "iso2Code": "AF",
                "name": "Afghanistan",
                "region": {"id": "SAS", "value": "South Asia"},
                "incomeLevel": {"id": "LIC", "value": "Low income"}
            },
            {
                "id": "BGD",
                "iso2Code": "BD",
                "name": "Bangladesh",
                "region": {"id": "SAS", "value": "South Asia"},
                "incomeLevel": {"id": "LMC", "value": "Lower middle income"}
            },
            {
                "id": "ZAF",
                "iso2Code": "ZA",
                "name": "South Africa",
                "region": {"id": "SSF", "value": "Sub-Saharan Africa"},
                "incomeLevel": {"id": "UMC", "value": "Upper middle income"}
            },
            {
                "id": "USA",
                "iso2Code": "US",
                "name": "United States",
                "region": {"id": "NAC", "value": "North America"},
                "incomeLevel": {"id": "HIC", "value": "High income"}
            }
        ]
    }

@pytest.fixture
def mock_wb_indicator_response():
    """Mock response for World Bank indicator API."""
    return {
        "page": 1,
        "pages": 1,
        "per_page": 500,
        "total": 150,
        "country": [
            {"countryiso3code": "AFG", "date": "2000", "value": 50.5, "unit": "", "obs_status": "", "decimal": 1},
            {"countryiso3code": "AFG", "date": "2001", "value": 50.3, "unit": "", "obs_status": "", "decimal": 1},
            {"countryiso3code": "BGD", "date": "2000", "value": 60.2, "unit": "", "obs_status": "", "decimal": 1},
        ]
    }

def test_get_world_bank_countries_by_income(mock_wb_countries_response):
    """Test fetching low/middle-income countries from World Bank."""
    with patch('data.fetch_record_counts.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_wb_countries_response
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        countries = get_world_bank_countries_by_income()

        # Should include AFG, BGD, ZAF but not USA (high income)
        assert "AFG" in countries
        assert "BGD" in countries
        assert "ZAF" in countries
        assert "USA" not in countries
        assert len(countries) == 3

def test_fetch_world_bank_records(mock_wb_indicator_response):
    """Test fetching record count from World Bank."""
    country_codes = ["AFG", "BGD", "ZAF"]
    
    with patch('data.fetch_record_counts.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_wb_indicator_response
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        record_count = fetch_world_bank_records(country_codes, "AG.LND.FRST.ZS")

        # Should return the total from metadata
        assert record_count == 150

def test_fetch_fao_records():
    """Test fetching record count from FAO."""
    country_codes = ["AFG", "BGD", "ZAF"]
    indicator_code = "AG.LND.FRST.ZS"

    # This is an estimate based on country * year combinations
    record_count = fetch_fao_records(country_codes, indicator_code)

    # 3 countries * 21 years (2000-2020) = 63
    assert record_count == 63

def test_save_outputs():
    """Test saving record counts to JSON file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_output.json"
        
        total_available = 1000
        total_merged = 800
        
        save_outputs(total_available, total_merged, output_path)
        
        # Verify file exists
        assert output_path.exists()
        
        # Verify content
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data["total_available"] == total_available
        assert data["total_merged"] == total_merged
        assert data["source"] == "FAO+WB"
        assert data["years"] == [2000, 2020]

@patch('data.fetch_record_counts.get_world_bank_countries_by_income')
@patch('data.fetch_record_counts.fetch_world_bank_records')
@patch('data.fetch_record_counts.fetch_fao_records')
@patch('data.fetch_record_counts.save_outputs')
def test_main(mock_save, mock_fao, mock_wb, mock_countries):
    """Test main function execution."""
    # Setup mocks
    mock_countries.return_value = ["AFG", "BGD", "ZAF"]
    mock_wb.return_value = 150
    mock_fao.return_value = 63
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Patch get_config to return a custom output path
        with patch('data.fetch_record_counts.get_config') as mock_config:
            mock_config.return_value = type('Config', (), {
                'data_dir': Path(tmpdir) / "data",
                'processed_dir': Path(tmpdir) / "data" / "processed"
            })()
            
            # Patch the output path directly
            with patch('data.fetch_record_counts.PROJECT_ROOT', Path(tmpdir)):
                main()
                
                # Verify save_outputs was called
                assert mock_save.called
                
                # Verify the arguments
                call_args = mock_save.call_args
                total_available, total_merged, output_path = call_args[0]
                
                # Total available should be sum of WB and FAO
                assert total_available == 150 + 63
                
                # Total merged should be 80% of min(150, 63) = 50
                assert total_merged == 50  # int(63 * 0.8) = 50