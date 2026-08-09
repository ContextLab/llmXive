"""
Unit tests for code/data/manifest_validator.py.
"""

import json
import os
import tempfile
import unittest

from code.data.manifest_validator import validate_manifest
from code.errors import ManifestError


class TestManifestValidator(unittest.TestCase):

    def setUp(self):
        """Create a temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()

    def _write_manifest(self, data: dict) -> str:
        """Helper to write a manifest dict to a temp file and return the path."""
        path = os.path.join(self.temp_dir, "test_manifest.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        return path

    def test_valid_manifest_with_doi(self):
        """Test that a manifest with valid DOI passes."""
        data = {
            "sources": [
                {"source_id": "src1", "doi": "10.1038/s41586-020-0001-x", "url": ""}
            ]
        }
        path = self._write_manifest(data)
        self.assertTrue(validate_manifest(path))

    def test_valid_manifest_with_url(self):
        """Test that a manifest with valid URL passes."""
        data = {
            "sources": [
                {"source_id": "src2", "doi": "", "url": "https://example.com/data"}
            ]
        }
        path = self._write_manifest(data)
        self.assertTrue(validate_manifest(path))

    def test_valid_manifest_with_both(self):
        """Test that a manifest with both DOI and URL passes."""
        data = {
            "sources": [
                {
                    "source_id": "src3",
                    "doi": "10.1038/s41586-020-0001-x",
                    "url": "https://example.com/data"
                }
            ]
        }
        path = self._write_manifest(data)
        self.assertTrue(validate_manifest(path))

    def test_invalid_manifest_missing_identifier(self):
        """Test that a manifest without DOI or URL raises ManifestError."""
        data = {
            "sources": [
                {"source_id": "src4", "doi": "", "url": ""}
            ]
        }
        path = self._write_manifest(data)
        with self.assertRaises(ManifestError) as context:
            validate_manifest(path)
        self.assertIn("FR-007 Violation", str(context.exception))
        self.assertIn("src4", str(context.exception))

    def test_invalid_manifest_no_doi_or_url_key(self):
        """Test that a manifest missing keys entirely raises ManifestError."""
        data = {
            "sources": [
                {"source_id": "src5", "checksum": "abc123"}
            ]
        }
        path = self._write_manifest(data)
        with self.assertRaises(ManifestError) as context:
            validate_manifest(path)
        self.assertIn("FR-007 Violation", str(context.exception))

    def test_invalid_manifest_whitespace_only(self):
        """Test that whitespace-only DOI/URL is treated as invalid."""
        data = {
            "sources": [
                {"source_id": "src6", "doi": "   ", "url": "   "}
            ]
        }
        path = self._write_manifest(data)
        with self.assertRaises(ManifestError) as context:
            validate_manifest(path)
        self.assertIn("FR-007 Violation", str(context.exception))

    def test_file_not_found(self):
        """Test that a missing file raises ManifestError."""
        with self.assertRaises(ManifestError) as context:
            validate_manifest("/nonexistent/path/to/manifest.json")
        self.assertIn("not found", str(context.exception))

    def test_invalid_json(self):
        """Test that invalid JSON raises ManifestError."""
        path = os.path.join(self.temp_dir, "bad.json")
        with open(path, 'w', encoding='utf-8') as f:
            f.write("{ invalid json }")
        with self.assertRaises(ManifestError) as context:
            validate_manifest(path)
        self.assertIn("Failed to parse manifest JSON", str(context.exception))

    def test_empty_sources_list(self):
        """Test that an empty sources list is valid (no violations)."""
        data = {"sources": []}
        path = self._write_manifest(data)
        self.assertTrue(validate_manifest(path))

    def test_multiple_sources_one_invalid(self):
        """Test that validation fails if ANY source in the list is invalid."""
        data = {
            "sources": [
                {"source_id": "good", "doi": "10.1000/test"},
                {"source_id": "bad", "url": ""}
            ]
        }
        path = self._write_manifest(data)
        with self.assertRaises(ManifestError) as context:
            validate_manifest(path)
        self.assertIn("bad", str(context.exception))

if __name__ == "__main__":
    unittest.main()