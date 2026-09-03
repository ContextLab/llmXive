"""
Unit tests for the versioning module.
"""
import os
import tempfile
import yaml
from pathlib import Path
from datetime import datetime, timezone

import pytest

from versioning import compute_file_sha256, hash_directory, update_state_file


def test_compute_file_sha256(tmp_path):
    """Test SHA256 computation on a simple file."""
    test_file = tmp_path / "test.txt"
    content = b"Hello, World!"
    test_file.write_bytes(content)
    
    hash_result = compute_file_sha256(test_file)
    
    assert isinstance(hash_result, str)
    assert len(hash_result) == 64  # SHA256 hex digest length
    # Verify it's a valid hex string
    int(hash_result, 16)


def test_hash_directory_empty(tmp_path):
    """Test hashing an empty directory."""
    result = hash_directory(tmp_path, tmp_path)
    assert result == {}


def test_hash_directory_with_files(tmp_path):
    """Test hashing a directory with files."""
    file1 = tmp_path / "file1.txt"
    file1.write_text("content1")
    
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    file2 = subdir / "file2.txt"
    file2.write_text("content2")
    
    result = hash_directory(tmp_path, tmp_path)
    
    assert len(result) == 2
    assert "file1.txt" in result
    assert "subdir/file2.txt" in result
    
    # Verify hashes are different for different content
    assert result["file1.txt"] != result["subdir/file2.txt"]


def test_hash_directory_nonexistent(tmp_path):
    """Test hashing a non-existent directory."""
    nonexistent = tmp_path / "does_not_exist"
    result = hash_directory(nonexistent, tmp_path)
    assert result == {}


def test_update_state_file_creates_new(tmp_path, monkeypatch):
    """Test that update_state_file creates a new state file if it doesn't exist."""
    monkeypatch.chdir(tmp_path)
    
    project_id = "TEST-PROJECT"
    data_hashes = {"data/file.txt": "abc123"}
    code_hashes = {"code/main.py": "def456"}
    
    update_state_file(project_id, data_hashes, code_hashes)
    
    state_file = tmp_path / "state" / "projects" / f"{project_id}.yaml"
    assert state_file.exists()
    
    with open(state_file, "r") as f:
        state_data = yaml.safe_load(f)
    
    assert state_data["project_id"] == project_id
    assert state_data["artifact_hashes"]["data"] == data_hashes
    assert state_data["artifact_hashes"]["code"] == code_hashes
    assert "updated_at" in state_data
    
    # Verify timestamp format
    datetime.fromisoformat(state_data["updated_at"].replace("Z", "+00:00"))


def test_update_state_file_updates_existing(tmp_path, monkeypatch):
    """Test that update_state_file updates an existing state file."""
    monkeypatch.chdir(tmp_path)
    
    project_id = "TEST-PROJECT"
    state_dir = tmp_path / "state" / "projects"
    state_dir.mkdir(parents=True)
    
    # Create initial state file
    initial_file = state_dir / f"{project_id}.yaml"
    initial_data = {
        "project_id": project_id,
        "artifact_hashes": {"old": "hash"},
        "updated_at": "2023-01-01T00:00:00+00:00"
    }
    with open(initial_file, "w") as f:
        yaml.dump(initial_data, f)
    
    # Update with new hashes
    new_data_hashes = {"new": "data"}
    new_code_hashes = {"new": "code"}
    update_state_file(project_id, new_data_hashes, new_code_hashes)
    
    with open(initial_file, "r") as f:
        updated_data = yaml.safe_load(f)
    
    assert updated_data["artifact_hashes"]["data"] == new_data_hashes
    assert updated_data["artifact_hashes"]["code"] == new_code_hashes
    assert updated_data["updated_at"] != initial_data["updated_at"]
    assert updated_data["project_id"] == project_id
