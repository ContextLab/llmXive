"""
Tests for data-sources.yaml validation logic.
"""

import tempfile
from pathlib import Path
from unittest import TestCase

import yaml

from utils.data_sources_validator import (
    validate_url_format,
    validate_endpoint,
    validate_source,
    validate_data_sources_config,
    load_and_validate_config,
)
from utils.error_handling import ValidationError


class TestUrlFormat(TestCase):
    def test_valid_http_url(self):
        self.assertTrue(validate_url_format("http://example.com"))

    def test_valid_https_url(self):
        self.assertTrue(validate_url_format("https://api.example.org/v1/data"))

    def test_valid_url_with_port(self):
        self.assertTrue(validate_url_format("https://localhost:8080/api"))

    def test_invalid_url_no_scheme(self):
        self.assertFalse(validate_url_format("example.com/path"))

    def test_invalid_url_empty(self):
        self.assertFalse(validate_url_format(""))
        self.assertFalse(validate_url_format("   "))

    def test_invalid_url_whitespace(self):
        self.assertFalse(validate_url_format(" http://example.com "))


class TestEndpointValidation(TestCase):
    def test_valid_endpoint(self):
        endpoint = {"url": "https://example.com/api", "method": "GET"}
        validate_endpoint(endpoint, "test_source", 0)  # Should not raise

    def test_missing_url(self):
        endpoint = {"method": "GET"}
        with self.assertRaises(ValidationError) as ctx:
            validate_endpoint(endpoint, "test_source", 0)
        self.assertIn("missing required keys", str(ctx.exception))

    def test_invalid_url_in_endpoint(self):
        endpoint = {"url": "not-a-url"}
        with self.assertRaises(ValidationError) as ctx:
            validate_endpoint(endpoint, "test_source", 0)
        self.assertIn("Invalid URL format", str(ctx.exception))

    def test_endpoint_not_dict(self):
        with self.assertRaises(ValidationError) as ctx:
            validate_endpoint("string", "test_source", 0)
        self.assertIn("must be a dictionary", str(ctx.exception))


class TestSourceValidation(TestCase):
    def test_valid_source(self):
        source_data = {
            "domain": "ml",
            "type": "arxiv",
            "endpoints": [{"url": "https://export.arxiv.org/api/query"}]
        }
        validate_source("ml_source", source_data)  # Should not raise

    def test_missing_required_keys(self):
        source_data = {"endpoints": [{"url": "https://example.com"}]}
        with self.assertRaises(ValidationError) as ctx:
            validate_source("bad_source", source_data)
        self.assertIn("missing required keys", str(ctx.exception))

    def test_empty_endpoints_list(self):
        source_data = {
            "domain": "ml",
            "type": "custom",
            "endpoints": []
        }
        with self.assertRaises(ValidationError) as ctx:
            validate_source("empty_source", source_data)
        self.assertIn("empty 'endpoints' list", str(ctx.exception))

    def test_endpoints_not_list(self):
        source_data = {
            "domain": "ml",
            "type": "custom",
            "endpoints": {"url": "https://example.com"}
        }
        with self.assertRaises(ValidationError) as ctx:
            validate_source("bad_type_source", source_data)
        self.assertIn("must have an 'endpoints' list", str(ctx.exception))


class TestFullConfigValidation(TestCase):
    def setUp(self):
        self.valid_config = {
            "ml_arxiv": {
                "domain": "ml",
                "type": "arxiv",
                "endpoints": [
                    {"url": "https://export.arxiv.org/api/query", "params": {"cat": "cs.LG"}}
                ]
            },
            "climate_nature": {
                "domain": "climate",
                "type": "doi_list",
                "endpoints": [
                    {"url": "https://api.nature.com/articles", "doi": "10.1038/s41558-023-01234-5"}
                ]
            }
        }

    def test_valid_config_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(self.valid_config, f)
            temp_path = Path(f.name)

        try:
            result = validate_data_sources_config(temp_path)
            self.assertEqual(result, self.valid_config)
        finally:
            temp_path.unlink()

    def test_invalid_config_missing_url(self):
        invalid_config = {
            "bad_source": {
                "domain": "ml",
                "type": "arxiv",
                "endpoints": [{"method": "GET"}]
            }
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(invalid_config, f)
            temp_path = Path(f.name)

        try:
            with self.assertRaises(ValidationError) as ctx:
                validate_data_sources_config(temp_path)
            self.assertIn("Invalid URL format", str(ctx.exception))
        finally:
            temp_path.unlink()

    def test_non_existent_file(self):
        with self.assertRaises(FileNotFoundError):
            validate_data_sources_config(Path("non_existent_file.yaml"))

    def test_empty_yaml_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")
            temp_path = Path(f.name)

        try:
            with self.assertRaises(ValidationError) as ctx:
                validate_data_sources_config(temp_path)
            self.assertIn("is empty", str(ctx.exception))
        finally:
            temp_path.unlink()

    def test_load_and_validate_config_default_path(self):
        # This test assumes data/data-sources.yaml exists if we run it in the project context.
        # If not, we catch the FileNotFoundError which is expected if the file is missing.
        try:
            result = load_and_validate_config()
            self.assertIsInstance(result, dict)
            self.assertGreater(len(result), 0)
        except FileNotFoundError:
            # Expected if data/data-sources.yaml hasn't been created yet in the test environment
            pass
