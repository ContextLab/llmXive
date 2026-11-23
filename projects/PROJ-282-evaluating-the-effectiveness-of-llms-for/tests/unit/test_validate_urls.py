import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.utils.validate_urls import (
    parse_research_manifest, validate_url_pattern, check_url_accessibility,
    validate_dataset_urls, validate_urls, main
)


class TestParseResearchManifest:
    def test_parse_valid_yaml(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("datasets:\n  - name: test\n    url: http://example.com\n")
            f.flush()
            manifest = parse_research_manifest(Path(f.name))
            assert len(manifest) == 1
            assert manifest[0]["name"] == "test"
        os.unlink(f.name)

class TestValidateUrlPattern:
    def test_valid_http_url(self):
        assert validate_url_pattern("http://example.com") is True
        assert validate_url_pattern("https://example.com") is True

    def test_invalid_url(self):
        assert validate_url_pattern("not-a-url") is False
        assert validate_url_pattern("ftp://example.com") is False  # Only http/https

class TestValidateDatasetUrls:
    @patch('src.utils.validate_urls.check_url_accessibility')
    def test_all_urls_accessible(self, mock_access):
        mock_access.return_value = True
        datasets = [
            {"name": "A", "url": "http://a.com"},
            {"name": "B", "url": "http://b.com"}
        ]
        result = validate_dataset_urls(datasets)
        assert result is True

    @patch('src.utils.validate_urls.check_url_accessibility')
    def test_one_url_fails(self, mock_access):
        mock_access.side_effect = [True, False]
        datasets = [
            {"name": "A", "url": "http://a.com"},
            {"name": "B", "url": "http://b.com"}
        ]
        result = validate_dataset_urls(datasets)
        assert result is False

class TestValidateUrls:
    @patch('src.utils.validate_urls.parse_research_manifest')
    @patch('src.utils.validate_urls.validate_dataset_urls')
    def test_full_validation_flow(self, mock_validate, mock_parse):
        mock_parse.return_value = [{"name": "X", "url": "http://x.com"}]
        mock_validate.return_value = True
        with tempfile.NamedTemporaryFile(suffix='.yaml') as f:
            result = validate_urls(Path(f.name))
            assert result is True
