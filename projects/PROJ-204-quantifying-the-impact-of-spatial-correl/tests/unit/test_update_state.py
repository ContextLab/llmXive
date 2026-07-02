"""
Unit tests for code/utils/update_state.py
"""
import os
import tempfile
import yaml
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module functions
# We need to adjust the import path based on how the project is structured.
# Assuming code/ is added to sys.path or run from root.
# For the test, we assume the module is importable as 'utils.update_state'
# relative to the code directory, or we import directly if code is in path.
# Given the task context, we assume 'code' is the root for imports or we patch sys.path.
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.update_state import (
    compute_file_hash,
    scan_data_directory,
    load_or_create_state,
    update_state_file,
    update_state,
    PROJECT_ID,
    STATE_DIR
)


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory with some test files."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "file1.txt").write_text("content1")
    (data_dir / "subdir").mkdir()
    (data_dir / "subdir" / "file2.csv").write_text("col1,col2\n1,2")
    return data_dir


@pytest.fixture
def temp_state_dir(tmp_path):
    """Create a temporary directory for state files."""
    state_dir = tmp_path / "state" / "projects"
    state_dir.mkdir(parents=True)
    return state_dir


def test_compute_file_hash(temp_data_dir):
    """Test that compute_file_hash returns the correct SHA-256 hash."""
    file_path = temp_data_dir / "file1.txt"
    expected_hash = hashlib.sha256(b"content1").hexdigest()
    actual_hash = compute_file_hash(file_path)
    assert actual_hash == expected_hash


def test_compute_file_hash_nonexistent():
    """Test that compute_file_hash raises an error for non-existent files."""
    with pytest.raises(FileNotFoundError):
        compute_file_hash(Path("nonexistent_file.txt"))


def test_scan_data_directory(temp_data_dir):
    """Test that scan_data_directory finds all files and computes hashes."""
    hashes = scan_data_directory(temp_data_dir)
    assert len(hashes) == 2
    assert "file1.txt" in hashes
    assert "subdir/file2.csv" in hashes
    # Verify hash correctness for one file
    expected_hash = hashlib.sha256(b"content1").hexdigest()
    assert hashes["file1.txt"] == expected_hash


def test_scan_data_directory_empty(temp_path):
    """Test scanning an empty directory."""
    data_dir = temp_path / "empty_data"
    data_dir.mkdir()
    hashes = scan_data_directory(data_dir)
    assert hashes == {}


def test_load_or_create_state_new(temp_state_dir):
    """Test loading a non-existent state file creates a new one in memory."""
    state_file = temp_state_dir / "new_project.yaml"
    state = load_or_create_state("new_project_id", state_file)
    assert state["project_id"] == "new_project_id"
    assert "artifact_hashes" in state


def test_load_or_create_state_existing(temp_state_dir):
    """Test loading an existing state file."""
    state_file = temp_state_dir / "existing_project.yaml"
    existing_data = {"project_id": "existing_id", "status": "done"}
    with open(state_file, "w") as f:
        yaml.dump(existing_data, f)

    state = load_or_create_state("existing_id", state_file)
    assert state["status"] == "done"
    assert state["project_id"] == "existing_id"


def test_update_state_file(temp_state_dir):
    """Test updating the state file with new hashes."""
    state_file = temp_state_dir / "update_test.yaml"
    initial_state = {"project_id": "test_id", "status": "init"}
    new_hashes = {"file.txt": "abc123"}

    update_state_file(initial_state, new_hashes, state_file)

    assert state_file.exists()
    with open(state_file, "r") as f:
        loaded = yaml.safe_load(f)
    assert loaded["artifact_hashes"] == new_hashes
    assert loaded["project_id"] == "test_id"


@patch('utils.update_state.DATA_DIR')
@patch('utils.update_state.STATE_DIR')
@patch('utils.update_state.logger')
def test_update_state_integration(mock_logger, mock_state_dir, mock_data_dir, temp_data_dir, temp_state_dir):
    """Integration test for the update_state function."""
    # Setup mocks
    mock_data_dir.exists.return_value = True
    mock_data_dir.rglob.return_value = [temp_data_dir / "file1.txt"]
    
    # We need to mock the specific paths used inside the function to point to our temp dirs
    # Since the function uses global constants, we patch the module's constants
    with patch('utils.update_state.DATA_DIR', temp_data_dir), \
         patch('utils.update_state.STATE_DIR', temp_state_dir.parent), \
         patch('utils.update_state.STATE_FILE', temp_state_dir / f"{PROJECT_ID}.yaml"):
        
        # Run the function
        update_state()

        # Verify the state file was created
        state_file = temp_state_dir / f"{PROJECT_ID}.yaml"
        assert state_file.exists()
        
        with open(state_file, "r") as f:
            state = yaml.safe_load(f)
        
        assert "artifact_hashes" in state
        assert len(state["artifact_hashes"]) > 0