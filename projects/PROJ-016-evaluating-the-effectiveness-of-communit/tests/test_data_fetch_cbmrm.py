import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import pytest

import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'code'))

from data.fetch_cbmrm_proxy import fetch_world_bank_indicator, validate_indicator_code, save_outputs
from config import YEAR_RANGE

@pytest.fixture
def mock_response_data():
    """Mock response data structure from World Bank API."""
    return [
        {"page": 1, "pages": 1, "per_page": 50, "total": 2},
        [
            {"countryiso3code": "USA", "date": "2020", "value": 33.5, "unit": "", "obs_status": "", "decimal": 1},
            {"countryiso3code": "CAN", "date": "2020", "value": 38.2, "unit": "", "obs_status": "", "decimal": 1},
            {"countryiso3code": "USA", "date": "2019", "value": 33.4, "unit": "", "obs_status": "", "decimal": 1},
            {"countryiso3code": "CAN", "date": "2019", "value": 38.1, "unit": "", "obs_status": "", "decimal": 1}
        ]
    ]

@patch('data.fetch_cbmrm_proxy.requests.get')
def test_fetch_world_bank_indicator_success(mock_get, mock_response_data):
    """Test successful fetching of World Bank indicator data."""
    mock_response = MagicMock()
    mock_response.json.return_value = mock_response_data
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    df = fetch_world_bank_indicator("AG.LND.FRST.ZS", 2019, 2020)

    assert len(df) == 4
    assert list(df.columns) == ['countryiso3code', 'date', 'value', 'unit', 'obs_status', 'decimal']
    assert df['countryiso3code'].unique().tolist() == ['USA', 'CAN']
    assert df['date'].unique().tolist() == ['2020', '2019']
    assert df['value'].mean() > 0

@patch('data.fetch_cbmrm_proxy.requests.get')
def test_fetch_world_bank_indicator_retry(mock_get):
    """Test retry logic on request failure."""
    mock_get.side_effect = [
        Exception("Connection Error"),
        Exception("Connection Error"),
        MagicMock(json=lambda: [{"page": 1, "pages": 1, "per_page": 50, "total": 2}, [{"countryiso3code": "USA", "date": "2020", "value": 33.5, "unit": "", "obs_status": "", "decimal": 1}]], raise_for_status=lambda: None)
    ]

    df = fetch_world_bank_indicator("AG.LND.FRST.ZS", 2020, 2020)

    assert len(df) == 1
    assert mock_get.call_count == 3

def test_validate_indicator_code(mock_response_data):
    """Test indicator code validation."""
    with patch('data.fetch_cbmrm_proxy.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = validate_indicator_code("AG.LND.FRST.ZS")
        assert result is True

def test_validate_indicator_code_no_data():
    """Test validation fails when no data is returned."""
    mock_empty_data = [{"page": 1, "pages": 1, "per_page": 50, "total": 0}, []]

    with patch('data.fetch_cbmrm_proxy.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_empty_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = validate_indicator_code("INVALID.CODE")
        assert result is False

def test_save_outputs():
    """Test saving outputs to CSV and JSON."""
    df = pd.DataFrame({
        'countryiso3code': ['USA', 'CAN'],
        'date': ['2020', '2020'],
        'value': [33.5, 38.2]
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        output_raw = tmp_path / "raw.csv"
        output_meta = tmp_path / "meta.json"

        save_outputs(df, "TEST.CODE", "http://example.com", output_raw, output_meta)

        assert output_raw.exists()
        assert output_meta.exists()

        # Check CSV content
        loaded_df = pd.read_csv(output_raw)
        assert len(loaded_df) == 2
        assert 'USA' in loaded_df['countryiso3code'].values

        # Check JSON content
        with open(output_meta) as f:
            metadata = json.load(f)
        
        assert metadata['indicator_code'] == "TEST.CODE"
        assert metadata['source_url'] == "http://example.com/TEST.CODE"
        assert 'fetch_date' in metadata
        assert metadata['record_count'] == 2