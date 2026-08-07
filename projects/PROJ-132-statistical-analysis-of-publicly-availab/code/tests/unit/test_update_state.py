import os
import tempfile
import json
import yaml
from pathlib import Path
import pytest

from src.data.update_state import (
    load_checksums_from_archive,
    update_state_file,
    run_state_update_pipeline
)


@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        archive_dir = root / "data" / "raw" / "archive"
        state_dir = root / "state" / "projects"
        archive_dir.mkdir(parents=True)
        state_dir.mkdir(parents=True)
        yield {
            "root": root,
            "archive": archive_dir,
            "state": state_dir
        }


def test_load_checksums_from_archive_success(temp_dirs):
    """Test loading checksums from a valid manifest."""
    archive_dir = temp_dirs["archive"]
    
    manifest_data = {
        "files": [
            {"path": "ebird_sample.parquet", "sha256": "abc123"},
            {"path": "climate_data.parquet", "sha256": "def456"}
        ]
    }
    
    manifest_path = archive_dir / "checksums.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f)
    
    checksums = load_checksums_from_archive(archive_dir)
    
    assert checksums == {
        "ebird_sample.parquet": "abc123",
        "climate_data.parquet": "def456"
    }


def test_load_checksums_from_archive_missing_file(temp_dirs):
    """Test that FileNotFoundError is raised when manifest is missing."""
    archive_dir = temp_dirs["archive"]
    
    with pytest.raises(FileNotFoundError, match="Checksum manifest not found"):
        load_checksums_from_archive(archive_dir)


def test_load_checksums_from_archive_invalid_json(temp_dirs):
    """Test that ValueError is raised when manifest is invalid JSON."""
    archive_dir = temp_dirs["archive"]
    manifest_path = archive_dir / "checksums.json"
    
    with open(manifest_path, 'w') as f:
        f.write("not valid json {{{")
    
    with pytest.raises(ValueError, match="Invalid JSON"):
        load_checksums_from_archive(archive_dir)


def test_update_state_file_creates_yaml(temp_dirs):
    """Test that update_state_file creates a valid YAML state file."""
    state_dir = temp_dirs["state"]
    project_id = "TEST-001"
    checksums = {
        "file1.parquet": "hash1",
        "file2.parquet": "hash2"
    }
    
    update_state_file(project_id, checksums, state_dir)
    
    state_file = state_dir / f"{project_id}.yaml"
    assert state_file.exists()
    
    with open(state_file, 'r') as f:
        data = yaml.safe_load(f)
    
    assert data["project_id"] == project_id
    assert data["artifact_hashes"] == checksums
    assert "updated_at" in data
    assert data["source"] == "T005e_update_state_pipeline"


def test_run_state_update_pipeline_end_to_end(temp_dirs):
    """Test the full pipeline: create manifest, load checksums, update state."""
    archive_dir = temp_dirs["archive"]
    state_dir = temp_dirs["state"]
    project_id = "TEST-002"
    
    # Create manifest
    manifest_data = {
        "files": [
            {"path": "raw_data.parquet", "sha256": "real_hash_123"}
        ]
    }
    with open(archive_dir / "checksums.json", 'w') as f:
        json.dump(manifest_data, f)
    
    # Run pipeline
    run_state_update_pipeline(project_id, archive_dir, state_dir)
    
    # Verify state file
    state_file = state_dir / f"{project_id}.yaml"
    assert state_file.exists()
    
    with open(state_file, 'r') as f:
        data = yaml.safe_load(f)
    
    assert data["artifact_hashes"] == {"raw_data.parquet": "real_hash_123"}