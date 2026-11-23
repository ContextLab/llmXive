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
from config import get_config

@pytest.fixture
def temp_data_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data"
        data_dir.mkdir()
        (data_dir / "raw").mkdir()
        (data_dir / "processed").mkdir()
        yield data_dir

@pytest.fixture
def mock_response_data():
    return [
        {"page": 1, "pages": 1, "per_page": 50, "total": 1},
        [
            {
                "id": "AG.LND.FRST.CF",
                "iso2code": "1W",
                "value": "Community Forestry Area Share",
                "source": {"id": "2", "value": "World Development Indicators"},
                "sourceNote": "Forest area is land under natural or planted stands of trees...",
                "sourceOrganization": "Food and Agriculture Organization",
                "topics": [{"id": "6", "value": "Environment"}]
            }
        ]
    ]

def test_validate_indicator_code(mock_response_data):
    with patch('data.fetch_cbmrm_proxy.fetch_with_backoff') as mock_fetch:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_fetch.return_value = mock_response

        result = validate_indicator_code("AG.LND.FRST.CF")
        assert result is True

def test_validate_indicator_code_no_data():
    with patch('data.fetch_cbmrm_proxy.fetch_with_backoff') as mock_fetch:
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"page": 1, "pages": 1, "per_page": 50, "total": 0},
            []
        ]
        mock_fetch.return_value = mock_response

        result = validate_indicator_code("NONEXISTENT.IND")
        assert result is False

def test_fetch_world_bank_indicator_success(temp_data_dir):
    mock_data = [
        {
            "page": 1, "pages": 1, "per_page": 50, "total": 2,
            "source": {"id": "2", "value": "World Development Indicators"}
        },
        [
            {"countryiso3code": "USA", "date": "2000", "value": 10.5},
            {"countryiso3code": "USA", "date": "2001", "value": 11.0},
            {"countryiso3code": "BRA", "date": "2000", "value": 20.0}
        ]
    ]

    with patch('data.fetch_cbmrm_proxy.fetch_with_backoff') as mock_fetch:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_data
        mock_fetch.return_value = mock_response

        df = fetch_world_bank_indicator("AG.LND.FRST.CF", 2000, 2020)
        
        assert not df.empty
        assert "countryiso3code" in df.columns
        assert "date" in df.columns
        assert "value" in df.columns
        assert len(df) == 3

def test_save_outputs(temp_data_dir):
    # Mock paths to use temp dir
    original_verify_path = Path("data/processed/verify_status_primary.json")
    original_proxy_path = Path("data/raw/cbnrm_proxy_primary.csv")
    original_metadata_path = Path("data/processed/cbnrm_proxy_metadata.json")
    
    # We will test the logic by checking file creation in the temp dir structure
    # But since the function uses hardcoded paths relative to project root,
    # we rely on the fixture creating the structure if we run in a temp env.
    # For this unit test, we just verify the function doesn't crash and creates files
    # if we assume the paths exist (which they do in the temp dir setup if we adjust CWD or mock paths).
    # To strictly test save_outputs without touching real FS, we would need to refactor.
    # Instead, we test the logic flow.
    
    # Create dummy df
    df = pd.DataFrame({"countryiso3code": ["USA"], "date": [2000], "value": [10.0]})
    
    # Save to temp paths for this test
    verify_path = temp_data_dir / "processed" / "verify_status_primary.json"
    proxy_path = temp_data_dir / "raw" / "cbnrm_proxy_primary.csv"
    metadata_path = temp_data_dir / "processed" / "cbnrm_proxy_metadata.json"
    
    # Temporarily override global paths (monkeypatch style for test)
    import data.fetch_cbmrm_proxy as mod
    mod.VERIFY_STATUS_PATH = verify_path
    mod.PROXY_DATA_PATH = proxy_path
    mod.METADATA_PATH = metadata_path

    save_outputs(True, "AG.LND.FRST.CF", df)

    assert verify_path.exists()
    assert proxy_path.exists()
    assert metadata_path.exists()

    with open(verify_path) as f:
        status = json.load(f)
        assert status["exists"] is True
        assert status["indicator"] == "AG.LND.FRST.CF"

    with open(metadata_path) as f:
        meta = json.load(f)
        assert meta["status"] == "success"

def test_main_halt_on_failure(temp_data_dir, caplog):
    # This test verifies that if the indicator is missing, main() logs a warning
    # and does not raise an exception (proceeds to fallback logic conceptually)
    
    # Setup temp paths
    import data.fetch_cbmrm_proxy as mod
    mod.VERIFY_STATUS_PATH = temp_data_dir / "processed" / "verify_status_primary.json"
    mod.PROXY_DATA_PATH = temp_data_dir / "raw" / "cbnrm_proxy_primary.csv"
    mod.METADATA_PATH = temp_data_dir / "processed" / "cbnrm_proxy_metadata.json"

    with patch('data.fetch_cbmrm_proxy.validate_indicator_code', return_value=False):
        # Should not raise
        main()
        
    # Verify verify_status_primary.json was created even if indicator missing
    assert mod.VERIFY_STATUS_PATH.exists()
    with open(mod.VERIFY_STATUS_PATH) as f:
        status = json.load(f)
        assert status["exists"] is False
        assert status["indicator"] == "AG.LND.FRST.CF"