"""
Unit tests for the update_state module.
"""
import os
import tempfile
import yaml
from pathlib import Path
import pytest

from utils.update_state import compute_file_hash, scan_data_directory, load_or_create_state, update_state_file


def test_compute_file_hash():
    """Test that file hashing works correctly."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test content")
        temp_path = Path(f.name)

    try:
        hash_val = compute_file_hash(temp_path)
        assert len(hash_val) == 64  # SHA-256 hex length
        assert isinstance(hash_val, str)
    finally:
        os.unlink(temp_path)


def test_scan_data_directory_empty():
    """Test scanning an empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_root = Path(tmpdir)
        result = scan_data_directory(data_root)
        assert result == {}


def test_scan_data_directory_with_files():
    """Test scanning a directory with files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_root = Path(tmpdir)
        file1 = data_root / "file1.txt"
        file2 = data_root / "subdir" / "file2.txt"
        
        file1.parent.mkdir(parents=True)
        file1.write_text("content1")
        file2.write_text("content2")

        result = scan_data_directory(data_root)
        
        assert "file1.txt" in result
        assert "subdir/file2.txt" in result
        assert len(result) == 2
        # Verify hashes are valid SHA-256
        for h in result.values():
            assert len(h) == 64


def test_load_or_create_state_new():
    """Test creating a new state file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "test.yaml"
        state = load_or_create_state("TEST-001", state_file)
        
        assert state["project_id"] == "TEST-001"
        assert state["status"] == "initialized"
        assert state["artifact_hashes"] == {}


def test_load_or_create_state_existing():
    """Test loading an existing state file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "test.yaml"
        initial_state = {
            "project_id": "TEST-002",
            "status": "running",
            "artifact_hashes": {"old.txt": "hash123"}
        }
        with open(state_file, "w") as f:
            yaml.dump(initial_state, f)

        state = load_or_create_state("TEST-002", state_file)
        
        assert state["project_id"] == "TEST-002"
        assert state["status"] == "running"
        assert state["artifact_hashes"] == {"old.txt": "hash123"}


def test_update_state_file():
    """Test updating and writing the state file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "test.yaml"
        state = {
            "project_id": "TEST-003",
            "status": "initialized",
            "artifact_hashes": {}
        }
        new_hashes = {"new.txt": "abc123"}

        update_state_file(state, new_hashes, state_file)

        assert state_file.exists()
        with open(state_file, "r") as f:
            written_state = yaml.safe_load(f)
        
        assert written_state["artifact_hashes"] == new_hashes
        assert written_state["project_id"] == "TEST-003"
