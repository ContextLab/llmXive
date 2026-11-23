import os
import yaml
import json
import tempfile
from pathlib import Path
from datetime import datetime

import pytest

from code.update_metadata import (
    ensure_dir,
    calculate_file_hash,
    update_metadata_with_download,
    update_project_state_with_artifact,
    init_metadata,
    init_project_state
)

class TestUpdateMetadata:
    def test_ensure_dir_creates_directory(self, tmp_path):
        """Test that ensure_dir creates a directory if it doesn't exist."""
        new_dir = tmp_path / "new" / "nested" / "dir"
        ensure_dir(new_dir)
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_ensure_dir_does_not_fail_if_exists(self, tmp_path):
        """Test that ensure_dir doesn't fail if directory already exists."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()
        ensure_dir(existing_dir)
        assert existing_dir.exists()

    def test_calculate_file_hash(self, tmp_path):
        """Test file hash calculation."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        hash_result = calculate_file_hash(test_file)
        
        # SHA256 of "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert hash_result == expected

    def test_calculate_file_hash_missing_file(self, tmp_path):
        """Test that calculate_file_hash raises FileNotFoundError for missing files."""
        missing_file = tmp_path / "nonexistent.txt"
        with pytest.raises(FileNotFoundError):
            calculate_file_hash(missing_file)

    def test_init_metadata(self):
        """Test metadata initialization."""
        metadata = init_metadata()
        assert "dataset_id" in metadata
        assert "version" in metadata
        assert "checksum" in metadata
        assert "download_date" in metadata

    def test_init_project_state(self):
        """Test project state initialization."""
        state = init_project_state()
        assert "project_id" in state
        assert "artifact_hashes" in state
        assert isinstance(state["artifact_hashes"], dict)

    def test_update_metadata_with_download(self, tmp_path):
        """Test updating metadata file."""
        metadata_file = tmp_path / "metadata.yaml"
        test_checksum = "abc123def456"
        test_date = "2023-01-01T00:00:00"
        
        update_metadata_with_download(
            metadata_file,
            "ds000246",
            "1.0.0",
            test_checksum,
            test_date
        )
        
        assert metadata_file.exists()
        with open(metadata_file, "r") as f:
            data = yaml.safe_load(f)
        
        assert data["dataset_id"] == "ds000246"
        assert data["version"] == "1.0.0"
        assert data["checksum"] == test_checksum
        assert data["download_date"] == test_date

    def test_update_project_state_with_artifact(self, tmp_path):
        """Test updating project state file."""
        state_file = tmp_path / "state.yaml"
        test_hash = "hash123456"
        
        # First call creates the file
        update_project_state_with_artifact(
            state_file,
            "test_artifact",
            test_hash
        )
        
        assert state_file.exists()
        with open(state_file, "r") as f:
            data = yaml.safe_load(f)
        
        assert data["project_id"] == "PROJ-228-investigating-the-impact-of-visual-compl"
        assert "test_artifact" in data["artifact_hashes"]
        assert data["artifact_hashes"]["test_artifact"]["hash"] == test_hash

    def test_update_project_state_updates_existing(self, tmp_path):
        """Test that updating project state adds new artifacts without removing old ones."""
        state_file = tmp_path / "state.yaml"
        
        update_project_state_with_artifact(
            state_file,
            "artifact1",
            "hash1"
        )
        
        update_project_state_with_artifact(
            state_file,
            "artifact2",
            "hash2"
        )
        
        with open(state_file, "r") as f:
            data = yaml.safe_load(f)
        
        assert "artifact1" in data["artifact_hashes"]
        assert "artifact2" in data["artifact_hashes"]
        assert data["artifact_hashes"]["artifact1"]["hash"] == "hash1"
        assert data["artifact_hashes"]["artifact2"]["hash"] == "hash2"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])