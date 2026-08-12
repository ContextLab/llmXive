import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd

from data.fetch_record_counts import get_world_bank_countries_by_income, fetch_world_bank_records, save_outputs

@pytest.fixture
def mock_wb_countries_response():
    return {
        "page": 1,
        "pages": 1,
        "per_page": 500,
        "total": 2,
        "country": [
            {"id": "AFG", "iso2Code": "AF", "name": "Afghanistan", "region": {"id": "SAS", "iso2code": "8S", "value": "South Asia"}, "adminregion": {"id": "SAS", "iso2code": "8S", "value": "South Asia"}, "incomeLevel": {"id": "LIC", "iso2code": "XM", "value": "Low income"}, "lendingType": {"id": "IDX", "iso2code": "XI", "value": "IDA"}, "capitalCity": "Kabul", "longitude": "69.1761", "latitude": "34.5228"},
            {"id": "ALB", "iso2Code": "AL", "name": "Albania", "region": {"id": "ECS", "iso2code": "ZJ", "value": "Europe & Central Asia"}, "adminregion": {"id": "ECS", "iso2code": "ZJ", "value": "Europe & Central Asia"}, "incomeLevel": {"id": "UMC", "iso2code": "XT", "value": "Upper middle income"}, "lendingType": {"id": "IBD", "iso2code": "XF", "value": "IBRD"}, "capitalCity": "Tirana", "longitude": "19.8172", "latitude": "41.3317"}
        ]
    }

@pytest.fixture
def mock_wb_indicator_response():
    return {
        "page": 1,
        "pages": 1,
        "per_page": 500,
        "total": 2,
        "data": [
            {"country": {"id": "AFG", "value": "AF"}, "countryiso3code": "AFG", "date": "2000", "value": 10.5, "unit": "", "obs_status": "", "decimal": 1},
            {"country": {"id": "ALB", "value": "AL"}, "countryiso3code": "ALB", "date": "2000", "value": None, "unit": "", "obs_status": "", "decimal": 1}
        ]
    }

def test_get_world_bank_countries_by_income(mock_wb_countries_response):
    with patch('data.fetch_record_counts.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_wb_countries_response
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        countries = get_world_bank_countries_by_income(["low", "lower_middle", "upper_middle"])

        assert len(countries) == 2
        assert countries[0]["id"] == "AFG"
        assert countries[1]["id"] == "ALB"

def test_fetch_world_bank_records(mock_wb_countries_response, mock_wb_indicator_response):
    with patch('data.fetch_record_counts.requests.get') as mock_get:
        # First call for countries
        mock_response_countries = MagicMock()
        mock_response_countries.json.return_value = mock_wb_countries_response
        mock_response_countries.raise_for_status = MagicMock()

        # Second call for indicator
        mock_response_indicator = MagicMock()
        mock_response_indicator.json.return_value = mock_wb_indicator_response
        mock_response_indicator.raise_for_status = MagicMock()

        mock_get.side_effect = [mock_response_countries, mock_response_indicator]

        count = fetch_world_bank_records([2000], ["low", "lower_middle", "upper_middle"])

        # Only 1 record has a non-null value (AFG)
        assert count == 1

def test_save_outputs():
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_output.json"
        save_outputs(100, output_path)

        assert output_path.exists()
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data["total_available_records"] == 100
        assert "year_range" in data
        assert "income_levels" in data
        assert "source" in data