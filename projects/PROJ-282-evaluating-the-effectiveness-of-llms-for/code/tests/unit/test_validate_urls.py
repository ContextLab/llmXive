"""
Unit tests for URL validation module (T005).
"""
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.utils.validate_urls import (
    parse_research_manifest,
    validate_url_pattern,
    check_url_accessibility,
    validate_dataset_urls,
    validate_urls
)

class TestParseResearchManifest:
    def test_parse_valid_manifest(self, tmp_path):
        """Test parsing a valid research.md file."""
        content = """
        # Research Data Sources

        ## VulDeePecker
        - URL: https://example.com/vuldeepecker.json

        ## BigVul
        - URL: https://example.com/bigvul.zip
        - URL: https://mirror.com/bigvul.tar.gz
        """
        manifest_file = tmp_path / "research.md"
        manifest_file.write_text(content)

        result = parse_research_manifest(manifest_file)

        assert "vuldeepecker" in result
        assert "bigvul" in result
        assert len(result["vuldeepecker"]["urls"]) == 1
        assert len(result["bigvul"]["urls"]) == 2
        assert result["bigvul"]["urls"][0] == "https://example.com/bigvul.zip"

    def test_parse_missing_file(self, tmp_path):
        """Test parsing a non-existent file."""
        result = parse_research_manifest(tmp_path / "nonexistent.md")
        assert result == {}

class TestValidateUrlPattern:
    def test_valid_http_url(self):
        is_valid, msg = validate_url_pattern("http://example.com/data")
        assert is_valid is True

    def test_valid_https_url(self):
        is_valid, msg = validate_url_pattern("https://example.com/data")
        assert is_valid is True

    def test_invalid_url_no_protocol(self):
        is_valid, msg = validate_url_pattern("example.com/data")
        assert is_valid is False
        assert "Invalid URL format" in msg

    def test_empty_url(self):
        is_valid, msg = validate_url_pattern("")
        assert is_valid is False

    def test_dataset_pattern_match(self):
        # URL contains dataset name
        is_valid, msg = validate_url_pattern("https://github.com/bigvul/dataset", "bigvul")
        assert is_valid is True

    def test_dataset_pattern_mismatch(self):
        # URL does not contain expected dataset name
        is_valid, msg = validate_url_pattern("https://github.com/other/dataset", "juliet")
        # This logs a warning but returns True for format validity
        assert is_valid is True

class TestCheckUrlAccessibility:
    @patch('src.utils.validate_urls.requests.head')
    def test_accessible_url(self, mock_head):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response

        is_accessible, msg = check_url_accessibility("https://example.com")
        assert is_accessible is True
        assert "Accessible" in msg

    @patch('src.utils.validate_urls.requests.head')
    def test_unaccessible_url(self, mock_head):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_head.return_value = mock_response

        is_accessible, msg = check_url_accessibility("https://example.com")
        assert is_accessible is False
        assert "Failed" in msg

    @patch('src.utils.validate_urls.requests.head')
    def test_timeout_error(self, mock_head):
        mock_head.side_effect = Exception("Timeout")

        is_accessible, msg = check_url_accessibility("https://example.com")
        assert is_accessible is False
        assert "Error" in msg or "Timeout" in msg

class TestValidateDatasetUrls:
    def test_validate_single_url(self):
        config = {
            'source': 'test_dataset',
            'urls': ['https://example.com/data']
        }
        
        # Mock the accessibility check to avoid real network calls
        with patch('src.utils.validate_urls.check_url_accessibility') as mock_check:
            mock_check.return_value = (True, "Accessible")
            
            results = validate_dataset_urls(config)
            
            assert len(results) == 1
            assert results[0]['dataset'] == 'test_dataset'
            assert results[0]['overall_valid'] is True

class TestValidateUrls:
    def test_validate_full_manifest(self, tmp_path):
        content = """
        ## TestDataset
        - URL: https://example.com/test
        """
        manifest_file = tmp_path / "research.md"
        manifest_file.write_text(content)

        with patch('src.utils.validate_urls.check_url_accessibility') as mock_check:
            mock_check.return_value = (True, "Accessible")
            
            results = validate_urls(manifest_file)
            
            assert results['status'] == 'success'
            assert results['total_urls'] == 1
            assert results['valid_urls'] == 1
            assert 'testdataset' in results['datasets']
            
    def test_validate_empty_manifest(self, tmp_path):
        content = "# No URLs here"
        manifest_file = tmp_path / "research.md"
        manifest_file.write_text(content)

        results = validate_urls(manifest_file)
        assert results['status'] == 'error'