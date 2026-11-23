"""
Unit test for retry logic in download.py
"""
import pytest
import time
import logging
from unittest.mock import patch, MagicMock, call
from pathlib import Path
import sys
import json

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from download import download_bulk_configs
from validators import validate_citations

@pytest.fixture
def mock_config_paths(tmp_path):
    """Create a temporary directory structure mimicking the project layout."""
    data_dir = tmp_path / "data"
    raw_dir = data_dir / "raw"
    raw_dir.mkdir(parents=True)
    
    # Create a mock metadata.yaml for validation
    metadata_content = """
    sources:
      - url: "https://materialsproject.org/materials/mp-123"
        description: "Test Fe-Cr bulk"
    """
    (data_dir / "metadata.yaml").write_text(metadata_content)
    
    return {
        "project_root": tmp_path,
        "data_paths": {
            "raw": raw_dir,
            "processed": data_dir / "processed",
            "backup": data_dir / "raw" / "backup"
        }
    }

def test_download_retry_logic_success_after_retries(mock_config_paths, caplog):
    """
    Test that download_bulk_configs retries on failure and succeeds eventually.
    """
    mock_url = "https://materialsproject.org/materials/mp-123"
    max_retries = 3
    
    call_count = 0
    def side_effect_validate(url, metadata_path):
        nonlocal call_count
        call_count += 1
        if call_count < max_retries:
            return {"success": False, "error_code": "URL_INVALID", "message": "Temporary failure"}
        return {"success": True, "error_code": None, "message": "OK"}

    with patch('download.validate_citations', side_effect=side_effect_validate) as mock_validate:
        with patch('download.requests.head') as mock_head:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_head.return_value = mock_response

            with patch('download.Path') as mock_path_class:
                mock_file_path = MagicMock()
                mock_path_class.return_value = mock_file_path
                mock_file_path.exists.return_value = False
                mock_file_path.parent.mkdir = MagicMock()

                with patch('download.open', MagicMock()):
                    with patch('download.json.dump'):
                        with patch('download.shutil.copyfileobj'):
                            with caplog.at_level(logging.INFO):
                                result = download_bulk_configs(mock_url, max_retries=max_retries)
                                assert mock_validate.call_count == max_retries
                                assert result is not None
                                assert result["success"] is True

def test_download_retry_logic_exhaustion(mock_config_paths, caplog):
    """
    Test that download_bulk_configs fails gracefully after max retries.
    """
    mock_url = "https://materialsproject.org/materials/mp-123"
    max_retries = 3
    
    def side_effect_validate(url, metadata_path):
        return {"success": False, "error_code": "URL_INVALID", "message": "Permanent failure"}

    with patch('download.validate_citations', side_effect=side_effect_validate):
        with patch('download.requests.head') as mock_head:
            mock_head.return_value = MagicMock(status_code=200)
            with caplog.at_level(logging.WARNING):
                result = download_bulk_configs(mock_url, max_retries=max_retries)
                assert result is not None
                assert result["success"] is False
                assert result.get("error_code") == "DATA_UNAVAILABLE"

def test_validate_citations_whitelist():
    """
    Test that validate_citations respects the whitelist.
    """
    from validators import validate_citations, VALIDATED_SOURCE_WHITELIST
    whitelisted_url = VALIDATED_SOURCE_WHITELIST[0]
    result = validate_citations(whitelisted_url, "dummy_path")
    assert result["success"] is True

def test_validate_citations_non_whitelisted():
    """
    Test that validate_citations rejects non-whitelisted URLs.
    """
    from validators import validate_citations
    non_whitelisted_url = "https://example.com/some-data"
    result = validate_citations(non_whitelisted_url, "dummy_path")
    assert result["success"] is False
    assert result["error_code"] == "URL_INVALID"

def test_manifest_creation_on_failure(mock_config_paths, tmp_path):
    """
    Test that inaccessible_manifest.json is created when downloads fail.
    """
    mock_url = "https://materialsproject.org/materials/mp-123"
    max_retries = 1
    
    def side_effect_validate(url, metadata_path):
        return {"success": False, "error_code": "URL_INVALID"}

    # We need to mock the paths since download_bulk_configs uses llmxive_toolkit.paths
    with patch('download.paths.data') as mock_paths_data:
        mock_raw_dir = tmp_path / "raw" / "oqmd_records"
        mock_paths_data.return_value = mock_raw_dir
        
        with patch('download.validate_citations', side_effect=side_effect_validate):
            with patch('download.requests.head'):
                download_bulk_configs(mock_url, max_retries=max_retries)
                
                # Check if manifest was created in the parent of the raw directory
                manifest_path = mock_raw_dir.parent / "inaccessible_manifest.json"
                assert manifest_path.exists(), "inaccessible_manifest.json should be created on failure"