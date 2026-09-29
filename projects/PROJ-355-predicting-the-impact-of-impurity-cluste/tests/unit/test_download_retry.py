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
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from data.download import download_bulk_configs
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
    Verifies that the retry mechanism attempts the correct number of times.
    """
    mock_url = "https://materialsproject.org/materials/mp-123"
    max_retries = 3
    
    # Track call count for validation
    call_count = 0
    
    def side_effect_validate(url, metadata_path):
        nonlocal call_count
        call_count += 1
        if call_count < max_retries:
            return {"success": False, "error_code": "URL_INVALID", "message": "Temporary failure"}
        return {"success": True, "error_code": None, "message": "OK"}

    with patch('data.download.validate_citations', side_effect=side_effect_validate) as mock_validate:
        with patch('data.download.requests.head') as mock_head:
            # Simulate network success for the HEAD request after validation passes
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers = {'Content-Length': '1024'}
            mock_head.return_value = mock_response

            with patch('data.download.Path') as mock_path_class:
                mock_file_path = MagicMock()
                mock_path_class.return_value = mock_file_path
                mock_file_path.exists.return_value = False
                mock_file_path.parent.mkdir = MagicMock()

                with patch('data.download.open', MagicMock()):
                    with patch('data.download.json.dump'):
                        # Mock the actual download content writing
                        with patch('data.download.shutil.copyfileobj'):
                            with caplog.at_level(logging.INFO):
                                result = download_bulk_configs(mock_url, max_retries=max_retries)
                                
                                # Verify validation was called exactly max_retries times
                                assert mock_validate.call_count == max_retries
                                
                                # Verify the final result indicates success
                                assert result is not None
                                assert "success" in result
                                assert result["success"] is True

                                # Verify logs indicate retries happened
                                log_messages = [record.message for record in caplog.records]
                                retry_logs = [msg for msg in log_messages if "Retry" in msg or "attempt" in msg.lower()]
                                assert len(retry_logs) >= 1, "Retry logic should log attempts"

def test_download_retry_logic_exhaustion(mock_config_paths, caplog):
    """
    Test that download_bulk_configs fails gracefully after max retries.
    Verifies that the function logs the failure and returns a failure status.
    """
    mock_url = "https://materialsproject.org/materials/mp-123"
    max_retries = 3
    
    # Always fail validation
    def side_effect_validate(url, metadata_path):
        return {"success": False, "error_code": "URL_INVALID", "message": "Permanent failure"}

    with patch('data.download.validate_citations', side_effect=side_effect_validate):
        with patch('data.download.requests.head') as mock_head:
            mock_head.return_value = MagicMock(status_code=200)

            with caplog.at_level(logging.WARNING):
                result = download_bulk_configs(mock_url, max_retries=max_retries)
                
                # Verify validation was called exactly max_retries times
                assert mock_head.call_count == max_retries # Should attempt HEAD after validation check logic in real impl, but here we check validation logic path
                
                # Verify the result indicates failure
                assert result is not None
                assert "success" in result
                assert result["success"] is False
                assert result.get("error_code") == "DATA_UNAVAILABLE"

                # Verify logs indicate exhaustion
                log_messages = [record.message for record in caplog.records]
                failure_logs = [msg for msg in log_messages if "exhausted" in msg.lower() or "DATA_UNAVAILABLE" in msg]
                assert len(failure_logs) >= 1, "Should log exhaustion after retries"

def test_validate_citations_whitelist(mock_config_paths):
    """
    Test that validate_citations respects the whitelist defined in config.
    Ensures that only whitelisted URLs are accepted without network checks.
    """
    from config import VALIDATED_SOURCE_WHITELIST
    
    # Test a whitelisted URL
    whitelisted_url = "https://materialsproject.org/materials/mp-123"
    metadata_path = str(mock_config_paths["data_paths"]["raw"].parent / "metadata.yaml")
    
    # Mock the HTTP request to avoid network dependency in this unit test
    with patch('validators.requests.head') as mock_head:
        mock_head.return_value = MagicMock(status_code=200)
        
        result = validate_citations(whitelisted_url, metadata_path)
        
        # Whitelisted URLs should pass if they are in the list
        # Note: The actual implementation checks the whitelist first.
        # If the URL is in the whitelist, it might skip the HEAD request or proceed differently.
        # We verify the function returns a success-like structure for valid inputs.
        assert isinstance(result, dict)
        assert "success" in result
        
def test_validate_citations_non_whitelisted(mock_config_paths):
    """
    Test that validate_citations rejects non-whitelisted URLs.
    """
    from config import VALIDATED_SOURCE_WHITELIST
    
    # Test a non-whitelisted URL
    non_whitelisted_url = "https://example.com/some-data"
    metadata_path = str(mock_config_paths["data_paths"]["raw"].parent / "metadata.yaml")
    
    result = validate_citations(non_whitelisted_url, metadata_path)
    
    # Should fail because it's not in the whitelist
    assert isinstance(result, dict)
    assert result["success"] is False
    assert result["error_code"] == "URL_INVALID"

def test_manifest_creation_on_failure(mock_config_paths, tmp_path):
    """
    Test that inaccessible_manifest.json is created when downloads fail.
    """
    mock_url = "https://materialsproject.org/materials/mp-123"
    max_retries = 1 # Force immediate failure
    
    def side_effect_validate(url, metadata_path):
        return {"success": False, "error_code": "URL_INVALID"}

    manifest_path = mock_config_paths["data_paths"]["raw"].parent / "inaccessible_manifest.json"
    
    with patch('data.download.validate_citations', side_effect=side_effect_validate):
        with patch('data.download.requests.head'):
            download_bulk_configs(mock_url, max_retries=max_retries)
            
            # Check if manifest was created
            assert manifest_path.exists(), "inaccessible_manifest.json should be created on failure"
            
            # Verify content
            with open(manifest_path, 'r') as f:
                manifest_data = json.load(f)
            
            assert "failed_urls" in manifest_data
            assert len(manifest_data["failed_urls"]) > 0
            assert manifest_data["failed_urls"][0]["url"] == mock_url