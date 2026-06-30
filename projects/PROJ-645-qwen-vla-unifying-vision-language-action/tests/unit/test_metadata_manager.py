"""
Unit tests for the metadata manager.
"""
import json
import os
import tempfile
from pathlib import Path
from datetime import datetime

import pytest
import yaml

# Import the module functions
# We need to adjust the import path since the test is in tests/unit
# and the code is in code/data
import sys
from pathlib import Path as SysPath

# Add the project root to the path if running as a standalone test
project_root = SysPath(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import the module from code/data
from code.data.metadata_manager import (
    get_schema,
    load_metadata,
    save_metadata,
    compute_checksum,
    initialize_schema_template,
    DATA_DIR,
    METADATA_FILE
)


class TestSchema:
    def test_get_schema_structure(self):
        """Verify the schema dictionary has expected keys."""
        schema = get_schema()
        assert "datasets" in schema
        assert "metadata_version" in schema
        assert "last_updated" in schema
        assert "properties" in schema["datasets"]
        
        props = schema["datasets"]["properties"]
        required_fields = ["version", "source", "created_at", "file_path", "status"]
        for field in required_fields:
            assert field in props


class TestChecksum:
    def test_compute_checksum(self, tmp_path):
        """Test SHA-256 checksum computation."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        checksum = compute_checksum(test_file)
        assert len(checksum) == 64
        assert all(c in "0123456789abcdef" for c in checksum)
        
        # Verify known hash for "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert checksum == expected


class TestMetadataIO:
    def test_load_nonexistent_metadata(self, tmp_path, monkeypatch):
        """Test loading when metadata file does not exist."""
        # Monkeypatch the global paths to use tmp_path
        monkeypatch.setattr("code.data.metadata_manager.DATA_DIR", tmp_path)
        monkeypatch.setattr("code.data.metadata_manager.METADATA_FILE", tmp_path / "metadata.yaml")
        
        data = load_metadata()
        assert "datasets" in data
        assert data["metadata_version"] == "1.0.0"
        assert "last_updated" in data

    def test_save_and_load_metadata(self, tmp_path, monkeypatch):
        """Test saving and loading metadata."""
        monkeypatch.setattr("code.data.metadata_manager.DATA_DIR", tmp_path)
        monkeypatch.setattr("code.data.metadata_manager.METADATA_FILE", tmp_path / "metadata.yaml")
        
        test_data = {
            "metadata_version": "1.0.0",
            "last_updated": "2023-01-01T00:00:00+00:00",
            "datasets": {
                "test_dataset": {
                    "version": "1.0.0",
                    "source": "test_source",
                    "created_at": "2023-01-01T00:00:00+00:00",
                    "checksum": "a" * 64,
                    "row_count": 100,
                    "file_path": "data/test.parquet",
                    "platforms": ["franka"],
                    "status": "draft"
                }
            }
        }
        
        save_metadata(test_data)
        loaded = load_metadata()
        
        assert loaded["datasets"]["test_dataset"]["version"] == "1.0.0"
        assert loaded["datasets"]["test_dataset"]["row_count"] == 100


class TestInitialization:
    def test_initialize_schema_template(self, tmp_path, monkeypatch):
        """Test that initialization creates a valid template."""
        monkeypatch.setattr("code.data.metadata_manager.DATA_DIR", tmp_path)
        monkeypatch.setattr("code.data.metadata_manager.METADATA_FILE", tmp_path / "metadata.yaml")
        
        initialize_schema_template()
        
        assert METADATA_FILE.exists()
        data = load_metadata()
        assert "datasets" in data
        assert isinstance(data["datasets"], dict)
        assert "metadata_version" in data
        assert "last_updated" in data
