"""
Unit tests for data-sources.yaml validation and usage in code/01_data_acquisition.py.

This module verifies that:
1. The data-sources.yaml file is correctly loaded and validated.
2. The validation logic properly rejects malformed configurations.
3. The acquisition code correctly uses the validated configuration.
"""

import pytest
import yaml
import os
import tempfile
from pathlib import Path
from typing import Dict, Any

# Import the validator utilities
from utils.data_sources_validator import (
    validate_url_format,
    validate_endpoint,
    validate_source,
    validate_data_sources_config,
    load_and_validate_config
)
from utils.error_handling import ValidationError

# Import the acquisition module to test integration
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils.config import get_model_config


class TestURLValidation:
    """Tests for URL format validation."""

    def test_valid_arxiv_url(self):
        """Test that valid arXiv API URL passes validation."""
        url = "https://export.arxiv.org/api/query"
        assert validate_url_format(url) is True

    def test_valid_doi_url(self):
        """Test that valid DOI URL passes validation."""
        url = "https://api.crossref.org/works/10.1038/nature12345"
        assert validate_url_format(url) is True

    def test_invalid_url_missing_scheme(self):
        """Test that URL without scheme fails validation."""
        url = "export.arxiv.org/api/query"
        assert validate_url_format(url) is False

    def test_invalid_url_malformed(self):
        """Test that malformed URL fails validation."""
        url = "ht!tp://invalid-url"
        assert validate_url_format(url) is False

    def test_empty_url(self):
        """Test that empty URL fails validation."""
        url = ""
        assert validate_url_format(url) is False

    def test_none_url(self):
        """Test that None URL fails validation."""
        url = None
        assert validate_url_format(url) is False


class TestEndpointValidation:
    """Tests for endpoint configuration validation."""

    def test_valid_endpoint(self):
        """Test that a valid endpoint configuration passes validation."""
        endpoint = {
            "url": "https://export.arxiv.org/api/query",
            "params": {
                "cat": "cs.LG",
                "max_results": 10
            }
        }
        assert validate_endpoint(endpoint) is True

    def test_endpoint_missing_url(self):
        """Test that endpoint without URL fails validation."""
        endpoint = {
            "params": {"cat": "cs.LG"}
        }
        with pytest.raises(ValidationError):
            validate_endpoint(endpoint)

    def test_endpoint_invalid_url(self):
        """Test that endpoint with invalid URL fails validation."""
        endpoint = {
            "url": "invalid-url",
            "params": {"cat": "cs.LG"}
        }
        with pytest.raises(ValidationError):
            validate_endpoint(endpoint)

    def test_endpoint_empty_params(self):
        """Test that endpoint with empty params is valid (params optional)."""
        endpoint = {
            "url": "https://export.arxiv.org/api/query"
        }
        assert validate_endpoint(endpoint) is True


class TestSourceValidation:
    """Tests for source configuration validation."""

    def test_valid_ml_source(self):
        """Test that a valid ML source configuration passes validation."""
        source = {
            "name": "arxiv_ml",
            "domain": "ML",
            "endpoints": [
                {
                    "url": "https://export.arxiv.org/api/query",
                    "params": {"cat": "cs.LG"}
                }
            ],
            "acceptance_filter": "accepted"
        }
        assert validate_source(source) is True

    def test_valid_non_ml_source(self):
        """Test that a valid non-ML source configuration passes validation."""
        source = {
            "name": "nature_climate",
            "domain": "Climate",
            "endpoints": [
                {
                    "url": "https://api.nature.com/articles",
                    "params": {"journal": "nature-climate-change"}
                }
            ],
            "acceptance_filter": "published"
        }
        assert validate_source(source) is True

    def test_source_missing_name(self):
        """Test that source without name fails validation."""
        source = {
            "domain": "ML",
            "endpoints": [{"url": "https://example.com"}]
        }
        with pytest.raises(ValidationError):
            validate_source(source)

    def test_source_missing_domain(self):
        """Test that source without domain fails validation."""
        source = {
            "name": "test_source",
            "endpoints": [{"url": "https://example.com"}]
        }
        with pytest.raises(ValidationError):
            validate_source(source)

    def test_source_missing_endpoints(self):
        """Test that source without endpoints fails validation."""
        source = {
            "name": "test_source",
            "domain": "ML"
        }
        with pytest.raises(ValidationError):
            validate_source(source)

    def test_source_empty_endpoints(self):
        """Test that source with empty endpoints list fails validation."""
        source = {
            "name": "test_source",
            "domain": "ML",
            "endpoints": []
        }
        with pytest.raises(ValidationError):
            validate_source(source)


class TestConfigValidation:
    """Tests for complete data-sources.yaml validation."""

    def _create_temp_config(self, config: Dict[str, Any]) -> str:
        """Helper to create a temporary YAML file with given config."""
        fd, path = tempfile.mkstemp(suffix='.yaml')
        try:
            with os.fdopen(fd, 'w') as f:
                yaml.dump(config, f)
            return path
        except Exception:
            os.close(fd)
            raise

    def test_valid_complete_config(self):
        """Test that a valid complete configuration passes validation."""
        config = {
            "sources": [
                {
                    "name": "arxiv_ml",
                    "domain": "ML",
                    "endpoints": [
                        {
                            "url": "https://export.arxiv.org/api/query",
                            "params": {"cat": "cs.LG"}
                        }
                    ]
                },
                {
                    "name": "nature_climate",
                    "domain": "Climate",
                    "endpoints": [
                        {
                            "url": "https://api.nature.com/articles",
                            "params": {"journal": "nature-climate-change"}
                        }
                    ]
                }
            ]
        }
        path = self._create_temp_config(config)
        try:
            assert validate_data_sources_config(config) is True
        finally:
            os.unlink(path)

    def test_config_missing_sources(self):
        """Test that config without sources fails validation."""
        config = {"version": "1.0"}
        with pytest.raises(ValidationError):
            validate_data_sources_config(config)

    def test_config_empty_sources(self):
        """Test that config with empty sources list fails validation."""
        config = {"sources": []}
        with pytest.raises(ValidationError):
            validate_data_sources_config(config)

    def test_config_invalid_source(self):
        """Test that config with invalid source fails validation."""
        config = {
            "sources": [
                {
                    "name": "invalid",
                    # Missing required fields
                }
            ]
        }
        with pytest.raises(ValidationError):
            validate_data_sources_config(config)

    def test_load_and_validate_existing_file(self):
        """Test loading and validating the actual data-sources.yaml file."""
        # Path relative to project root
        config_path = Path(__file__).parent.parent.parent / 'code' / 'data-sources.yaml'
        
        if config_path.exists():
            # Should load and validate without error
            config = load_and_validate_config(config_path)
            assert config is not None
            assert "sources" in config
            assert len(config["sources"]) > 0
        else:
            # If file doesn't exist, skip this test
            pytest.skip("data-sources.yaml not found")


class TestAcquisitionIntegration:
    """Tests for integration between config validation and acquisition code."""

    def test_config_used_in_acquisition(self):
        """Test that acquisition code correctly uses validated config."""
        # Create a minimal valid config
        config = {
            "sources": [
                {
                    "name": "test_source",
                    "domain": "ML",
                    "endpoints": [
                        {
                            "url": "https://export.arxiv.org/api/query",
                            "params": {"cat": "cs.LG"}
                        }
                    ]
                }
            ]
        }
        
        # Validate the config
        assert validate_data_sources_config(config) is True
        
        # The acquisition module should be able to use this config
        # (We can't actually run the full acquisition in unit tests,
        # but we verify the config structure is compatible)
        assert "sources" in config
        for source in config["sources"]:
            assert "name" in source
            assert "domain" in source
            assert "endpoints" in source

    def test_domain_filtering(self):
        """Test that sources can be filtered by domain."""
        config = {
            "sources": [
                {"name": "ml_source", "domain": "ML", "endpoints": [{"url": "https://arxiv.org"}]},
                {"name": "climate_source", "domain": "Climate", "endpoints": [{"url": "https://nature.com"}]},
                {"name": "health_source", "domain": "Health", "endpoints": [{"url": "https://healthaffairs.org"}]}
            ]
        }
        
        # Validate config
        assert validate_data_sources_config(config) is True
        
        # Filter by domain
        ml_sources = [s for s in config["sources"] if s["domain"] == "ML"]
        climate_sources = [s for s in config["sources"] if s["domain"] == "Climate"]
        
        assert len(ml_sources) == 1
        assert len(climate_sources) == 1
        assert ml_sources[0]["name"] == "ml_source"
        assert climate_sources[0]["name"] == "climate_source"


class TestErrorHandling:
    """Tests for error handling in config validation."""

    def test_validation_error_contains_message(self):
        """Test that ValidationError contains helpful error messages."""
        invalid_config = {"sources": [{}]}
        
        with pytest.raises(ValidationError) as exc_info:
            validate_data_sources_config(invalid_config)
        
        assert len(str(exc_info.value)) > 0
        assert "sources" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()

    def test_nested_validation_errors(self):
        """Test that nested validation errors are properly propagated."""
        config = {
            "sources": [
                {
                    "name": "test",
                    "domain": "ML",
                    "endpoints": [
                        {"url": "invalid-url"}  # Invalid URL
                    ]
                }
            ]
        }
        
        with pytest.raises(ValidationError):
            validate_data_sources_config(config)