"""
Unit tests for src/utils/validate_urls.py
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys_path = Path(__file__).resolve().parent.parent.parent
if str(sys_path) not in os.sys.path:
    os.sys.path.insert(0, str(sys_path))

from src.utils.validate_urls import (
    URL_PATTERN,
    validate_url_accessibility,
    validate_dataset_urls,
    load_research_manifest,
    URLValidationError
)

class TestURLPattern:
    def test_valid_http(self):
        assert URL_PATTERN.match("http://example.com")
        assert URL_PATTERN.match("http://example.com/path?query=1")
    
    def test_valid_https(self):
        assert URL_PATTERN.match("https://github.com/user/repo")
    
    def test_invalid(self):
        assert not URL_PATTERN.match("ftp://example.com")
        assert not URL_PATTERN.match("not-a-url")
        assert not URL_PATTERN.match("http://")

class TestValidateURLAccessibility:
    @patch('src.utils.validate_urls.requests.head')
    def test_accessible(self, mock_head):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response
        
        is_valid, msg = validate_url_accessibility("http://example.com")
        assert is_valid is True
        assert "Accessible" in msg

    @patch('src.utils.validate_urls.requests.head')
    def test_redirect(self, mock_head):
        mock_response = MagicMock()
        mock_response.status_code = 302
        mock_head.return_value = mock_response
        
        is_valid, msg = validate_url_accessibility("http://example.com")
        assert is_valid is True
        assert "Redirected" in msg

    @patch('src.utils.validate_urls.requests.head')
    def test_not_found(self, mock_head):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_head.return_value = mock_response
        
        is_valid, msg = validate_url_accessibility("http://example.com")
        assert is_valid is False
        assert "404" in msg

    @patch('src.utils.validate_urls.requests.head')
    def test_connection_error(self, mock_head):
        mock_head.side_effect = Exception("Connection failed")
        
        is_valid, msg = validate_url_accessibility("http://example.com")
        assert is_valid is False
        assert "Request failed" in msg

class TestValidateDatasetURLs:
    def test_empty_manifest(self):
        with pytest.raises(ValueError, match="No datasets found"):
            validate_dataset_urls([])

    def test_dict_manifest(self):
        manifest = {
            "vuldeepecker": "http://valid-url.com",
            "juliet": "http://another-valid.com"
        }
        # We mock the actual request to avoid network dependency in unit tests
        with patch('src.utils.validate_urls.validate_url_accessibility') as mock_validate:
            mock_validate.return_value = (True, "Accessible")
            results = validate_dataset_urls(manifest)
            
            assert "vuldeepecker" in results
            assert "juliet" in results
            assert results["vuldeepecker"]["valid"] is True
            assert results["juliet"]["valid"] is True

    def test_list_manifest(self):
        manifest = [
            {"name": "ds1", "url": "http://url1.com"},
            {"name": "ds2", "url": "http://url2.com"}
        ]
        with patch('src.utils.validate_urls.validate_url_accessibility') as mock_validate:
            mock_validate.return_value = (True, "Accessible")
            results = validate_dataset_urls(manifest)
            
            assert "ds1" in results
            assert "ds2" in results

class TestLoadResearchManifest:
    @patch('src.utils.validate_urls.RESEARCH_MD_PATH')
    def test_yaml_block_found(self, mock_path):
        mock_content = """
        # Research
        ```yaml
        dataset_manifest:
          - name: test_ds
            url: http://test.com
        ```
        """
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = mock_content
        
        manifest = load_research_manifest()
        assert isinstance(manifest, dict)
        assert "dataset_manifest" in manifest
        assert len(manifest["dataset_manifest"]) == 1

    @patch('src.utils.validate_urls.RESEARCH_MD_PATH')
    def test_file_not_found(self, mock_path):
        mock_path.exists.return_value = False
        with pytest.raises(FileNotFoundError):
            load_research_manifest()

    @patch('src.utils.validate_urls.RESEARCH_MD_PATH')
    def test_no_manifest_key(self, mock_path):
        mock_content = """
        # Research
        Some text without yaml block
        """
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = mock_content
        
        with pytest.raises(ValueError, match="Could not find"):
            load_research_manifest()