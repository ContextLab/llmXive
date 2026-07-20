"""
Unit tests for the state_manager module.
"""
import os
import tempfile
import yaml
from pathlib import Path
import pytest
from datetime import datetime

# We need to mock get_project_root for testing
import sys
from unittest.mock import patch, MagicMock

# Create a temporary directory for test state files
@pytest.fixture
def temp_project_root():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Create necessary subdirectories
        (tmp_path / "data").mkdir()
        (tmp_path / "data" / "processed").mkdir()
        (tmp_path / "data" / "final").mkdir()
        # Create a dummy file to register
        test_file = tmp_path / "data" / "processed" / "test_file.txt"
        test_file.write_text("test content")
        yield tmp_path
        # Cleanup happens automatically

@pytest.fixture
def mock_get_project_root(temp_project_root):
    with patch('state_manager.get_project_root', return_value=temp_project_root):
        with patch('config.get_project_root', return_value=temp_project_root):
            yield temp_project_root

def test_compute_file_checksum(mock_get_project_root):
    """Test that checksum is computed correctly and consistently."""
    from state_manager import _compute_file_checksum

    file_path = mock_get_project_root / "data" / "processed" / "test_file.txt"
    checksum1 = _compute_file_checksum(file_path)
    checksum2 = _compute_file_checksum(file_path)

    assert checksum1 == checksum2
    assert len(checksum1) == 64  # SHA-256 hex length
    assert all(c in '0123456789abcdef' for c in checksum1)

def test_load_state_empty(mock_get_project_root):
    """Test loading state when file doesn't exist."""
    from state_manager import load_state

    state = load_state()

    assert "metadata" in state
    assert "files" in state
    assert state["metadata"]["version"] == "1.0"
    assert state["files"] == {}

def test_load_state_with_data(mock_get_project_root):
    """Test loading state when file exists."""
    from state_manager import load_state, save_state

    # Create a state file
    test_state = {
        "metadata": {
            "version": "1.0",
            "created_at": "2024-01-01T00:00:00",
            "last_updated": "2024-01-01T00:00:00"
        },
        "files": {
            "data/processed/test.txt": {
                "path": "data/processed/test.txt",
                "checksum": "abc123",
                "size_bytes": 100
            }
        }
    }

    state_path = mock_get_project_root / "state.yaml"
    with open(state_path, "w") as f:
        yaml.dump(test_state, f)

    loaded_state = load_state()
    assert loaded_state["metadata"]["version"] == "1.0"
    assert "data/processed/test.txt" in loaded_state["files"]

def test_register_file(mock_get_project_root):
    """Test registering a file."""
    from state_manager import register_file, load_state

    file_path = "data/processed/test_file.txt"
    state = register_file(file_path)

    assert file_path in state["files"]
    assert "checksum" in state["files"][file_path]
    assert "size_bytes" in state["files"][file_path]
    assert "registered_at" in state["files"][file_path]

def test_register_nonexistent_file(mock_get_project_root):
    """Test that registering a non-existent file raises an error."""
    from state_manager import register_file

    with pytest.raises(FileNotFoundError):
        register_file("data/processed/nonexistent.txt")

def test_verify_file_valid(mock_get_project_root):
    """Test verifying a valid file."""
    from state_manager import register_file, verify_file

    file_path = "data/processed/test_file.txt"
    state = register_file(file_path)
    state = register_file(file_path, state)  # Ensure it's in state

    # Save state
    from state_manager import save_state
    save_state(state)

    assert verify_file(file_path) is True

def test_verify_file_modified(mock_get_project_root):
    """Test verifying a file that has been modified."""
    from state_manager import register_file, verify_file, save_state

    file_path = "data/processed/test_file.txt"
    state = register_file(file_path)
    save_state(state)

    # Modify the file
    test_file = mock_get_project_root / file_path
    test_file.write_text("modified content")

    assert verify_file(file_path) is False

def test_verify_all(mock_get_project_root):
    """Test verifying all files."""
    from state_manager import register_file, save_state, verify_all

    file1 = "data/processed/test_file.txt"
    state = register_file(file1)

    file2_path = mock_get_project_root / "data" / "processed" / "test2.txt"
    file2_path.write_text("test2")
    file2 = "data/processed/test2.txt"
    state = register_file(file2, state)
    save_state(state)

    results = verify_all()
    assert file1 in results
    assert file2 in results
    assert results[file1] is True
    assert results[file2] is True

def test_get_file_info(mock_get_project_root):
    """Test getting file info."""
    from state_manager import register_file, get_file_info

    file_path = "data/processed/test_file.txt"
    state = register_file(file_path)

    info = get_file_info(file_path, state)
    assert info is not None
    assert info["path"] == file_path
    assert "checksum" in info

def test_clear_stale_entries(mock_get_project_root):
    """Test clearing stale entries."""
    from state_manager import register_file, save_state, clear_stale_entries

    file_path = "data/processed/test_file.txt"
    state = register_file(file_path)

    # Add a fake entry for a non-existent file
    state["files"]["data/processed/deleted_file.txt"] = {
        "path": "data/processed/deleted_file.txt",
        "checksum": "fake",
        "size_bytes": 0
    }
    save_state(state)

    new_state = clear_stale_entries()
    assert "data/processed/deleted_file.txt" not in new_state["files"]
    assert file_path in new_state["files"]
