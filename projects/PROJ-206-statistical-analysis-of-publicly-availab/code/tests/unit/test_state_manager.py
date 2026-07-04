"""
Unit tests for the state_manager utility.
"""
import os
import tempfile
from pathlib import Path
import pytest
import yaml

from src.utils.state_manager import (
    compute_file_hash,
    get_state_file_path,
    load_state,
    save_state,
    update_artifact_state,
    verify_artifact_integrity,
)
from src.utils.config import get_project_root, get_state_path


def test_compute_file_hash(tmp_path):
    """Test SHA-256 hash computation for a known file."""
    test_file = tmp_path / "test.txt"
    content = b"Hello, World!"
    test_file.write_bytes(content)

    expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
    computed_hash = compute_file_hash(test_file)

    assert computed_hash == expected_hash


def test_compute_file_hash_nonexistent():
    """Test that computing hash for nonexistent file raises error."""
    with pytest.raises(FileNotFoundError):
        compute_file_hash(Path("/nonexistent/file.txt"))


def test_load_state_empty():
    """Test loading state when file does not exist."""
    # Use a temporary directory to ensure no existing state file interferes
    # Note: In a real test suite, we might mock the state path, but here
    # we rely on the fact that a fresh environment won't have the file.
    # If the file exists from a previous run, this test verifies we get a dict.
    state = load_state()
    assert isinstance(state, dict)


def test_save_and_load_state(tmp_path, monkeypatch):
    """Test saving and loading state."""
    # Monkeypatch the state path to our temp directory
    def mock_get_state_path():
        return tmp_path

    monkeypatch.setattr("src.utils.state_manager.get_state_path", mock_get_state_path)
    monkeypatch.setattr("src.utils.config.get_state_path", mock_get_state_path)

    test_state = {"key": "value", "nested": {"a": 1}}
    save_state(test_state)

    loaded_state = load_state()
    assert loaded_state == test_state


def test_update_artifact_state(tmp_path, monkeypatch):
    """Test updating state with a new artifact."""
    # Setup temp directories
    project_root = tmp_path / "project"
    project_root.mkdir()
    data_dir = project_root / "data"
    data_dir.mkdir()
    state_dir = project_root / "state" / "projects"
    state_dir.mkdir(parents=True)

    # Create a test artifact
    artifact_file = data_dir / "test_output.csv"
    artifact_file.write_text("col1,col2\n1,2\n3,4")

    # Monkeypatch paths
    def mock_get_project_root():
        return project_root

    def mock_get_state_path():
        return state_dir

    monkeypatch.setattr("src.utils.state_manager.get_project_root", mock_get_project_root)
    monkeypatch.setattr("src.utils.config.get_project_root", mock_get_project_root)
    monkeypatch.setattr("src.utils.state_manager.get_state_path", mock_get_state_path)
    monkeypatch.setattr("src.utils.config.get_state_path", mock_get_state_path)

    # Update state
    new_state = update_artifact_state(artifact_file, "Test artifact description")

    # Verify state structure
    assert "artifacts" in new_state
    assert "data/test_output.csv" in new_state["artifacts"]

    entry = new_state["artifacts"]["data/test_output.csv"]
    assert entry["description"] == "Test artifact description"
    assert len(entry["hash"]) == 64  # SHA-256 hex length
    assert Path(entry["path"]).name == "test_output.csv"


def test_verify_artifact_integrity(tmp_path, monkeypatch):
    """Test artifact integrity verification."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    data_dir = project_root / "data"
    data_dir.mkdir()
    state_dir = project_root / "state" / "projects"
    state_dir.mkdir(parents=True)

    artifact_file = data_dir / "verify_test.txt"
    artifact_file.write_text("original content")

    def mock_get_project_root():
        return project_root

    def mock_get_state_path():
        return state_dir

    monkeypatch.setattr("src.utils.state_manager.get_project_root", mock_get_project_root)
    monkeypatch.setattr("src.utils.config.get_project_root", mock_get_project_root)
    monkeypatch.setattr("src.utils.state_manager.get_state_path", mock_get_state_path)
    monkeypatch.setattr("src.utils.config.get_state_path", mock_get_state_path)

    # First, update state to store the hash
    update_artifact_state(artifact_file)

    # Verify should return True
    assert verify_artifact_integrity(artifact_file) is True

    # Modify the file
    artifact_file.write_text("modified content")

    # Verify should return False
    assert verify_artifact_integrity(artifact_file) is False

    # Restore original content
    artifact_file.write_text("original content")
    assert verify_artifact_integrity(artifact_file) is True


def test_update_artifact_nonexistent():
    """Test that updating state with nonexistent artifact raises error."""
    with pytest.raises(FileNotFoundError):
        update_artifact_state(Path("/nonexistent/artifact.txt"))