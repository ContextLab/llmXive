"""
Tests for code/generate_manifest.py
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module under test
# We need to add the project root to sys.path to import 'generate_manifest'
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from generate_manifest import generate_manifest, write_manifest, get_file_metadata, MANIFEST_PATH, MASTER_DATASET_PATH


class TestGetFileMetadata:
    def test_file_exists(self, tmp_path):
        test_file = tmp_path / "test.csv"
        test_file.write_text("a,b\n1,2\n3,4")
        meta = get_file_metadata(test_file)
        assert meta["exists"] is True
        assert "size_bytes" in meta
        assert meta["row_count"] == 2

    def test_file_missing(self, tmp_path):
        missing_file = tmp_path / "nonexistent.csv"
        meta = get_file_metadata(missing_file)
        assert meta["exists"] is False
        assert "error" in meta

    def test_csv_row_count(self, tmp_path):
        test_file = tmp_path / "data.csv"
        # Header + 3 rows
        test_file.write_text("col1,col2\nval1,val2\nval3,val4\nval5,val6")
        meta = get_file_metadata(test_file)
        assert meta["row_count"] == 3

class TestGenerateManifest:
    def test_manifest_structure(self):
        manifest = generate_manifest()
        assert "generated_at" in manifest
        assert "project_id" in manifest
        assert "api_endpoints" in manifest
        assert "ingestion_parameters" in manifest
        assert "artifacts" in manifest

        # Check API config keys
        api = manifest["api_endpoints"]
        assert api["provider"] == "GitHub REST API"
        assert "base_url" in api

        # Check ingestion params
        params = manifest["ingestion_parameters"]
        assert "min_prs_12m" in params
        assert params["min_prs_12m"] == 10

    def test_artifact_entry(self):
        manifest = generate_manifest()
        artifacts = manifest["artifacts"]
        assert isinstance(artifacts, list)
        assert len(artifacts) >= 1
        assert artifacts[0]["name"] == "master_dataset.csv"
        assert "path" in artifacts[0]

class TestWriteManifest:
    def test_write_json(self, tmp_path):
        test_manifest = {"key": "value", "nested": {"a": 1}}
        output_file = tmp_path / "manifest.json"
        write_manifest(test_manifest, output_file)
        
        assert output_file.exists()
        with open(output_file, 'r') as f:
            loaded = json.load(f)
        assert loaded == test_manifest