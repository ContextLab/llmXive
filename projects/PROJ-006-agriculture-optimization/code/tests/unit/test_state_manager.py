"""
Unit tests for src.utils.state_manager.
"""

import os
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# We need to mock the PROJECT_ROOT and state file path to avoid affecting the real project
# or requiring the full project structure to exist for tests.
# However, the module uses absolute paths derived from __file__.
# To test properly, we will patch the module-level constants or use a temporary directory
# and inject it. Since the module is already imported with specific paths,
# we will test the logic by mocking the filesystem interactions.

from src.utils.state_manager import (
    compute_file_hash,
    scan_directory_for_artifacts,
    load_state,
    save_state,
    update_artifact_hashes,
    verify_artifacts,
    STATE_FILE,
    PROJECT_ROOT
)
from src.utils.io_helpers import FatalError

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_compute_file_hash(temp_dir):
    """Test SHA-256 hash computation."""
    test_file = temp_dir / "test.txt"
    content = b"Hello, World!"
    test_file.write_bytes(content)

    expected_hash = hashlib.sha256(content).hexdigest()
    actual_hash = compute_file_hash(test_file)

    assert actual_hash == expected_hash

def test_compute_file_hash_missing(temp_dir):
    """Test that compute_file_hash raises FatalError for missing files."""
    missing_file = temp_dir / "nonexistent.txt"

    with pytest.raises(FatalError):
        compute_file_hash(missing_file)

def test_scan_directory_for_artifacts(temp_dir):
    """Test artifact scanning logic."""
    # Create structure
    (temp_dir / "raw").mkdir()
    (temp_dir / "processed").mkdir()

    # Create files with supported extensions
    (temp_dir / "raw" / "data.csv").touch()
    (temp_dir / "raw" / "info.json").touch()
    (temp_dir / "raw" / "ignored.log").touch() # .log is supported
    (temp_dir / "processed" / "results.parquet").touch()
    (temp_dir / "processed" / "notes.md").touch() # .md is NOT supported

    artifacts = scan_directory_for_artifacts(temp_dir)

    # Check expected files are found
    paths = [str(p) for p in artifacts]
    assert str(temp_dir / "raw" / "data.csv") in paths
    assert str(temp_dir / "raw" / "info.json") in paths
    assert str(temp_dir / "raw" / "ignored.log") in paths
    assert str(temp_dir / "processed" / "results.parquet") in paths
    assert str(temp_dir / "processed" / "notes.md") not in paths

def test_scan_directory_nonexistent(temp_dir):
    """Test scanning a non-existent directory returns empty list."""
    nonexistent = temp_dir / "does_not_exist"
    artifacts = scan_directory_for_artifacts(nonexistent)
    assert artifacts == []

def test_load_state_missing_file(temp_dir):
    """Test load_state returns default dict when file is missing."""
    # Mock the STATE_FILE to point to a non-existent file in temp_dir
    with patch('src.utils.state_manager.STATE_FILE', temp_dir / "missing.yaml"):
        state = load_state()
        assert "project_id" in state
        assert state["project_id"] == "PROJ-006-agriculture-optimization"
        assert state["artifacts"] == {}

def test_save_state_and_load(temp_dir):
    """Test saving and loading state."""
    test_file = temp_dir / "test_state.yaml"
    test_state = {
        "project_id": "TEST-001",
        "last_updated": "2023-01-01",
        "artifacts": {"data.csv": "hash123"}
    }

    with patch('src.utils.state_manager.STATE_FILE', test_file):
        with patch('src.utils.state_manager.STATE_DIR', temp_dir):
            save_state(test_state)

            loaded_state = load_state()
            assert loaded_state == test_state

def test_update_artifact_hashes_integration(temp_dir, monkeypatch):
    """
    Integration test for update_artifact_hashes using a mock structure.
    We patch the module's directory constants to point to our temp_dir.
    """
    # Setup temp structure
    data_raw = temp_dir / "data" / "raw"
    data_processed = temp_dir / "data" / "processed"
    state_dir = temp_dir / "state" / "projects"

    data_raw.mkdir(parents=True)
    data_processed.mkdir(parents=True)
    state_dir.mkdir(parents=True)

    # Create test files
    test_file_raw = data_raw / "survey.csv"
    test_file_raw.write_bytes(b"col1,col2\n1,2\n")

    test_file_processed = data_processed / "analysis.json"
    test_file_processed.write_bytes(b'{"key": "value"}')

    # Patch the module constants
    monkeypatch.setattr('src.utils.state_manager.PROJECT_ROOT', temp_dir)
    monkeypatch.setattr('src.utils.state_manager.STATE_DIR', state_dir)
    monkeypatch.setattr('src.utils.state_manager.STATE_FILE', state_dir / "PROJ-006-agriculture-optimization.yaml")
    monkeypatch.setattr('src.utils.state_manager.DATA_RAW_DIR', data_raw)
    monkeypatch.setattr('src.utils.state_manager.DATA_PROCESSED_DIR', data_processed)

    # Run update
    result = update_artifact_hashes()

    # Verify result
    assert len(result) == 2
    assert "data/raw/survey.csv" in result
    assert "data/processed/analysis.json" in result

    # Verify state file was created
    state_file = state_dir / "PROJ-006-agriculture-optimization.yaml"
    assert state_file.exists()

def test_verify_artifacts(temp_dir, monkeypatch):
    """Test verify_artifacts logic."""
    # Setup
    data_raw = temp_dir / "data" / "raw"
    data_raw.mkdir(parents=True)
    test_file = data_raw / "test.csv"
    content = b"test"
    test_file.write_bytes(content)
    expected_hash = hashlib.sha256(content).hexdigest()

    state_dir = temp_dir / "state" / "projects"
    state_dir.mkdir(parents=True)
    state_file = state_dir / "PROJ-006-agriculture-optimization.yaml"

    # Mock state
    mock_state = {
        "project_id": "PROJ-006-agriculture-optimization",
        "last_updated": "now",
        "artifacts": {
            "data/raw/test.csv": expected_hash,
            "data/raw/missing.csv": "fake_hash"
        }
    }

    # Patch
    monkeypatch.setattr('src.utils.state_manager.PROJECT_ROOT', temp_dir)
    monkeypatch.setattr('src.utils.state_manager.STATE_DIR', state_dir)
    monkeypatch.setattr('src.utils.state_manager.STATE_FILE', state_file)
    monkeypatch.setattr('src.utils.state_manager.DATA_RAW_DIR', data_raw)
    monkeypatch.setattr('src.utils.state_manager.DATA_PROCESSED_DIR', temp_dir / "data" / "processed")

    # Save mock state
    with open(state_file, "w") as f:
        import yaml
        yaml.dump(mock_state, f)

    # Test
    # 1. All valid (if we remove the missing one from check or ensure it exists)
    # Let's test the missing case
    is_valid = verify_artifacts()
    assert is_valid is False # Because data/raw/missing.csv is missing

    # 2. Verify specific existing file
    is_valid_specific = verify_artifacts(["data/raw/test.csv"])
    assert is_valid_specific is True
