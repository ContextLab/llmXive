import pytest
import yaml
import json
from pathlib import Path
import tempfile
import os

from update_metadata import (
    ensure_dir,
    init_metadata,
    init_project_state,
    update_metadata_with_download
)

def test_ensure_dir_creates_directory():
    """Test that ensure_dir creates the directory if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir) / "subdir" / "nested" / "file.txt"
        ensure_dir(test_path)
        assert test_path.parent.exists()

def test_init_metadata_creates_file():
    """Test that init_metadata creates the metadata file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_path = Path(tmpdir) / "metadata.yaml"
        
        init_metadata(
            dataset_id="ds000246",
            version="1.0.0",
            checksum="abc123",
            download_date="2024-01-01T00:00:00",
            metadata_path=metadata_path
        )
        
        assert metadata_path.exists()
        
        with open(metadata_path, 'r') as f:
            metadata = yaml.safe_load(f)
        
        assert metadata["dataset_id"] == "ds000246"
        assert metadata["version"] == "1.0.0"
        assert metadata["checksum"] == "abc123"
        assert metadata["download_date"] == "2024-01-01T00:00:00"

def test_init_project_state_creates_file():
    """Test that init_project_state creates the state file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "state.yaml"
        artifact_hashes = {"ds000246": "abc123"}
        
        init_project_state(
            project_id="PROJ-228",
            artifact_hashes=artifact_hashes,
            state_path=state_path
        )
        
        assert state_path.exists()
        
        with open(state_path, 'r') as f:
            state = yaml.safe_load(f)
        
        assert state["project_id"] == "PROJ-228"
        assert state["artifact_hashes"] == artifact_hashes
        assert "updated_at" in state

def test_update_metadata_with_download_updates_both_files():
    """Test that update_metadata_with_download updates both metadata and state files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_path = Path(tmpdir) / "metadata.yaml"
        state_path = Path(tmpdir) / "state.yaml"
        artifact_hashes = {"ds000246": "abc123"}
        
        update_metadata_with_download(
            dataset_id="ds000246",
            version="1.0.0",
            checksum="abc123",
            project_id="PROJ-228",
            artifact_hashes=artifact_hashes,
            metadata_path=metadata_path,
            state_path=state_path
        )
        
        # Check metadata file
        assert metadata_path.exists()
        with open(metadata_path, 'r') as f:
            metadata = yaml.safe_load(f)
        
        assert metadata["dataset_id"] == "ds000246"
        assert metadata["version"] == "1.0.0"
        assert metadata["checksum"] == "abc123"
        assert "download_date" in metadata
        
        # Check state file
        assert state_path.exists()
        with open(state_path, 'r') as f:
            state = yaml.safe_load(f)
        
        assert state["project_id"] == "PROJ-228"
        assert state["artifact_hashes"] == artifact_hashes
        assert "updated_at" in state
