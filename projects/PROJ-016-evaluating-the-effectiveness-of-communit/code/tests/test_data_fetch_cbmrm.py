"""
Tests for T009: Fetch CBNRM Proxy.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import pytest
import sys
import os

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from data.fetch_cbmrm_proxy import (
    fetch_world_bank_indicator,
    validate_indicator_code,
    save_outputs,
    main,
    TARGET_INDICATORS,
    YEARS
)

@pytest.fixture
def mock_response_data():
    """Mock World Bank API response data."""
    return [
        {}, # Metadata (empty for simplicity)
        [
            {
                "countryiso3code": "USA",
                "date": "2000",
                "value": 10.5,
                "unit": "Index",
                "obs_status": ""
            },
            {
                "countryiso3code": "USA",
                "date": "2001",
                "value": 11.0,
                "unit": "Index",
                "obs_status": ""
            },
            {
                "countryiso3code": "BRA",
                "date": "2000",
                "value": 8.2,
                "unit": "Index",
                "obs_status": ""
            }
        ]
    ]

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_fetch_world_bank_indicator_success(mock_response_data):
    """Test successful fetch of World Bank indicator."""
    with patch('data.fetch_cbmrm_proxy.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = fetch_world_bank_indicator("IC.LGL.CRED.XQ", YEARS)

        assert result is not None
        assert len(result) == 3 # Metadata + 3 records
        mock_get.assert_called_once()

def test_fetch_world_bank_indicator_retry():
    """Test retry logic on failure (simplified)."""
    with patch('data.fetch_cbmrm_proxy.requests.get') as mock_get:
        mock_get.side_effect = [
            Exception("Connection Error"),
            Exception("Connection Error"),
            Exception("Connection Error")
        ]

        result = fetch_world_bank_indicator("IC.LGL.CRED.XQ", YEARS)
        assert result is None
        assert mock_get.call_count == 3

def test_validate_indicator_code(mock_response_data):
    """Test validation of indicator code."""
    records = mock_response_data[1]
    assert validate_indicator_code(records, "IC.LGL.CRED.XQ") is True

def test_validate_indicator_code_no_data():
    """Test validation when data is all null."""
    records = [
        {
            "countryiso3code": "USA",
            "date": "2000",
            "value": None,
            "unit": "Index",
            "obs_status": ""
        }
    ]
    assert validate_indicator_code(records, "IC.LGL.CRED.XQ") is False

def test_save_outputs(temp_data_dir, mock_response_data):
    """Test saving outputs to CSV and JSON."""
    records = mock_response_data[1]
    indicator_code = "IC.LGL.CRED.XQ"
    source_url = "https://api.worldbank.org/v2/country/all/indicator/IC.LGL.CRED.XQ"
    validation_status = True

    save_outputs(records, indicator_code, source_url, validation_status, temp_data_dir)

    # Check CSV exists
    csv_path = temp_data_dir.parent / "raw" / "cbnrm_proxy.csv"
    assert csv_path.exists()

    # Check JSON exists
    json_path = temp_data_dir / "cbnrm_proxy_metadata.json"
    assert json_path.exists()

    # Verify JSON content
    with open(json_path, 'r') as f:
        metadata = json.load(f)
    assert metadata["indicator_code"] == indicator_code
    assert metadata["validation_status"] is True
    assert metadata["records_fetched"] == len(records)

def test_main_halt_on_failure(temp_data_dir):
    """Test that main() halts if no indicator is found."""
    # Mock fetch to return None for all indicators
    with patch('data.fetch_cbmrm_proxy.fetch_world_bank_indicator', return_value=None):
        with patch('data.fetch_cbmrm_proxy.sys.exit') as mock_exit:
            # We need to patch the loop to ensure it tries all
            with patch.object(data.fetch_cbmrm_proxy, 'TARGET_INDICATORS', ['FAKE.IND']):
                main()
                mock_exit.assert_called_once_with(1)
