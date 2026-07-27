"""
Tests for the manifest generation module.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Adjust import path for testing context
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from generate_manifest import get_file_metadata, generate_manifest, write_manifest


class TestGetFileMetadata:
    def test_existing_file(self, tmp_path):
        """Test metadata extraction for an existing file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("line 1\nline 2\nline 3")

        metadata = get_file_metadata(test_file)

        assert metadata["exists"] is True
        assert metadata["line_count"] == 3
        assert "size_bytes" in metadata
        assert "modified_timestamp" in metadata

    def test_non_existing_file(self, tmp_path):
        """Test metadata extraction for a non-existing file."""
        missing_file = tmp_path / "missing.txt"

        metadata = get_file_metadata(missing_file)

        assert metadata["exists"] is False
        assert "missing.txt" in metadata["path"]


class TestWriteManifest:
    def test_write_json(self, tmp_path):
        """Test writing a manifest to a JSON file."""
        test_manifest = {
            "version": "1.0.0",
            "data": [1, 2, 3]
        }
        output_path = tmp_path / "manifest.json"

        write_manifest(test_manifest, output_path)

        assert output_path.exists()
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        assert loaded == test_manifest


class TestGenerateManifest:
    @patch("generate_manifest.get_config")
    @patch("generate_manifest.PROJECT_ROOT", new_callable=lambda: Path(__file__).parent.parent)
    def test_manifest_structure(self, mock_root, mock_config):
        """Test that the generated manifest has the required structure."""
        mock_config.return_value = {"github_api_base": "https://api.github.com"}

        manifest = generate_manifest()

        assert "version" in manifest
        assert "project_id" in manifest
        assert "generated_at" in manifest
        assert "pipeline" in manifest
        assert "inputs" in manifest["pipeline"]
        assert "outputs" in manifest["pipeline"]
        assert "endpoints" in manifest["pipeline"]
        assert "execution_context" in manifest

        # Check endpoints are documented
        assert len(manifest["pipeline"]["endpoints"]) > 0
        endpoint_names = [e["name"] for e in manifest["pipeline"]["endpoints"]]
        assert "ingest_repositories" in endpoint_names
        assert "run_analysis" in endpoint_names
