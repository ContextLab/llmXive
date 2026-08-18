"""
Unit tests for the state_manager module.
"""

import os
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import yaml

import sys
# Ensure the code directory is in the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.utils.state_manager import (
    compute_file_hash,
    scan_directory_for_artifacts,
    load_state,
    save_state,
    update_artifact_hashes,
    verify_artifacts
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_file(temp_dir):
    """Create a sample file for hashing tests."""
    file_path = temp_dir / "test_file.txt"
    content = b"Hello, World! This is a test file."
    file_path.write_bytes(content)
    return file_path


def test_compute_file_hash(sample_file):
    """Test that compute_file_hash returns the correct SHA-256 hash."""
    expected_hash = hashlib.sha256(b"Hello, World! This is a test file.").hexdigest()
    actual_hash = compute_file_hash(sample_file)
    assert actual_hash == expected_hash


def test_compute_file_hash_missing(temp_dir):
    """Test that compute_file_hash raises FileNotFoundError for missing files."""
    missing_file = temp_dir / "nonexistent.txt"
    with pytest.raises(FileNotFoundError):
        compute_file_hash(missing_file)


def test_scan_directory_for_artifacts(temp_dir):
    """Test scanning a directory for artifacts."""
    # Create test files
    (temp_dir / "file1.csv").touch()
    (temp_dir / "file2.parquet").touch()
    (temp_dir / "file3.txt").touch()

    # Scan all files
    all_files = scan_directory_for_artifacts(temp_dir)
    assert len(all_files) == 3

    # Scan only CSV files
    csv_files = scan_directory_for_artifacts(temp_dir, extensions=[".csv"])
    assert len(csv_files) == 1
    assert csv_files[0].name == "file1.csv"


def test_scan_directory_nonexistent():
    """Test scanning a non-existent directory raises an error."""
    with pytest.raises(NotADirectoryError):
        scan_directory_for_artifacts(Path("/nonexistent/path"))


def test_load_state_missing_file(temp_dir):
    """Test loading a missing state file returns default state."""
    missing_path = temp_dir / "missing.yaml"
    state = load_state(missing_path)
    assert state["project_id"] == ""
    assert state["artifacts"] == {}


def test_save_state_and_load(temp_dir):
    """Test saving and loading state preserves data."""
    state_path = temp_dir / "test_state.yaml"
    test_state = {
        "project_id": "TEST-001",
        "artifacts": {"raw": {"file1.csv": "hash1"}},
        "last_updated": "2023-01-01"
    }

    save_state(test_state, state_path)
    loaded_state = load_state(state_path)

    assert loaded_state["project_id"] == "TEST-001"
    assert loaded_state["artifacts"]["raw"]["file1.csv"] == "hash1"


def test_update_artifact_hashes_integration(temp_dir):
    """Test updating artifact hashes in a state file."""
    # Setup directories
    raw_dir = temp_dir / "data" / "raw"
    raw_dir.mkdir(parents=True)
    state_path = temp_dir / "state.yaml"

    # Create a sample artifact
    sample_file = raw_dir / "sample.csv"
    sample_file.write_bytes(b"col1,col2\n1,2\n")

    # Update hashes
    project_id = "TEST-UPDATE"
    hashes = update_artifact_hashes(project_id, state_path, [raw_dir])

    # Verify results
    assert len(hashes) == 1
    assert "data/raw/sample.csv" in hashes

    # Verify state file content
    with open(state_path, "r") as f:
        state = yaml.safe_load(f)

    assert state["project_id"] == project_id
    assert "data/raw/sample.csv" in state["artifacts"]["raw"]


def test_verify_artifacts(temp_dir):
    """Test verifying artifact integrity."""
    # Setup
    raw_dir = temp_dir / "data" / "raw"
    raw_dir.mkdir(parents=True)
    state_path = temp_dir / "state.yaml"

    # Create a file
    sample_file = raw_dir / "sample.csv"
    sample_file.write_bytes(b"col1,col2\n1,2\n")

    # Compute initial hash
    initial_hash = compute_file_hash(sample_file)

    # Save state with initial hash
    test_state = {
        "project_id": "TEST-VERIFY",
        "artifacts": {"raw": {"data/raw/sample.csv": initial_hash}},
        "last_updated": ""
    }
    save_state(test_state, state_path)

    # Verify (should pass)
    results = verify_artifacts(state_path, [raw_dir])
    assert results["data/raw/sample.csv"] is True

    # Modify file
    sample_file.write_bytes(b"modified content")

    # Verify again (should fail)
    results = verify_artifacts(state_path, [raw_dir])
    assert results["data/raw/sample.csv"] is False
