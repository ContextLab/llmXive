import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import pytest
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.fetch_cbmrm_proxy import validate_indicator_code, fetch_world_bank_indicator, save_outputs, main

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_dir = Path(tmpdir) / "raw"
        processed_dir = Path(tmpdir) / "processed"
        raw_dir.mkdir()
        processed_dir.mkdir()
        yield {
            "raw": raw_dir,
            "processed": processed_dir,
            "base": Path(tmpdir)
        }

@pytest.fixture
def mock_response_data():
    """Mock World Bank API response data."""
    return {
        "page": 1,
        "pages": 1,
        "per_page": 5000,
        "total": 2
    }, [
        {
            "id": "AG.LND.FRST.CF",
            "iso2Code": "XX",
            "name": "Community Forestry Area Share",
            "source": {
                "id": "2",
                "value": "World Development Indicators"
            },
            "sourceNote": "Percentage of forest area under community management",
            "sourceOrganization": "World Bank",
            "topics": []
        }
    ]

def test_validate_indicator_code(mock_response_data):
    """Test that validate_indicator_code returns True for valid indicator."""
    with patch('data.fetch_cbmrm_proxy.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value=mock_response_data)
        mock_get.return_value = mock_response
        
        result = validate_indicator_code("AG.LND.FRST.CF")
        assert result is True
        mock_get.assert_called_once()

def test_validate_indicator_code_no_data():
    """Test that validate_indicator_code returns False when indicator not found."""
    with patch('data.fetch_cbmrm_proxy.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value=[{"page": 1, "pages": 1, "per_page": 1, "total": 0}, []])
        mock_get.return_value = mock_response
        
        result = validate_indicator_code("INVALID.INDICATOR.CODE")
        assert result is False

def test_fetch_world_bank_indicator_success(temp_data_dir):
    """Test successful fetch of World Bank indicator data."""
    mock_data = {
        "page": 1,
        "pages": 1,
        "per_page": 2,
        "total": 2
    }, [
        {
            "countryiso3code": "USA",
            "date": "2000",
            "value": 15.5,
            "country": {"id": "US", "value": "United States"}
        },
        {
            "countryiso3code": "USA",
            "date": "2001",
            "value": 16.2,
            "country": {"id": "US", "value": "United States"}
        }
    ]
    
    with patch('data.fetch_cbmrm_proxy.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value=mock_data)
        mock_get.return_value = mock_response
        
        df = fetch_world_bank_indicator("AG.LND.FRST.CF", 2000, 2020)
        
        assert df is not None
        assert len(df) == 2
        assert "USA" in df["country_code"].values
        assert 2000 in df["year"].values
        assert 2001 in df["year"].values

def test_save_outputs(temp_data_dir):
    """Test that save_outputs creates correct CSV and JSON files."""
    df = pd.DataFrame({
        "country_code": ["USA", "CAN"],
        "country_name": ["United States", "Canada"],
        "year": [2000, 2000],
        "value": [15.5, 10.2],
        "indicator_code": ["AG.LND.FRST.CF", "AG.LND.FRST.CF"]
    })
    
    raw_path = temp_data_dir["raw"] / "cbnrm_proxy.csv"
    metadata_path = temp_data_dir["processed"] / "cbnrm_proxy_metadata.json"
    
    save_outputs(df, "AG.LND.FRST.CF", raw_path, metadata_path)
    
    assert raw_path.exists()
    assert metadata_path.exists()
    
    # Verify CSV content
    saved_df = pd.read_csv(raw_path)
    assert len(saved_df) == 2
    assert "USA" in saved_df["country_code"].values
    
    # Verify JSON content
    with open(metadata_path, "r") as f:
        metadata = json.load(f)
    
    assert metadata["status"] == "success"
    assert metadata["indicator"] == "AG.LND.FRST.CF"
    assert metadata["rows_fetched"] == 2

def test_main_halt_on_failure(temp_data_dir):
    """Test that main returns 1 when indicator verification fails."""
    with patch('data.fetch_cbmrm_proxy.validate_indicator_code', return_value=False):
        # Mock config to use our temp directories
        with patch('data.fetch_cbmrm_proxy.get_config') as mock_config:
            mock_config.return_value = {
                "API_BASE_URL": "https://api.worldbank.org/v2",
                "WB_CBNRM_INDICATOR": "AG.LND.FRST.CF",
                "DATA_YEARS_START": 2000,
                "DATA_YEARS_END": 2020
            }
            
            # Patch Path to use temp directories
            original_path = Path.__new__
            def mock_path_new(cls, *args, **kwargs):
                if args and str(args[0]).endswith("fetch_cbmrm_proxy.py"):
                    # Return a path that points to temp dir for parent resolution
                    return original_path(cls, str(temp_data_dir["base"] / "code" / "data" / "fetch_cbmrm_proxy.py"))
                return original_path(cls, *args, **kwargs)
            
            with patch.object(Path, '__new__', mock_path_new):
                result = main()
                assert result == 1