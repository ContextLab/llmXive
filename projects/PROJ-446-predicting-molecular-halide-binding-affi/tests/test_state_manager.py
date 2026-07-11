"""
Tests for the state manager module.
"""
import os
import json
import tempfile
import yaml
from pathlib import Path

import pytest

from code.utils.state_manager import (
    calculate_file_hash,
    calculate_directory_hash,
    load_state_yaml,
    save_state_yaml,
    update_artifact_hash,
    set_simulated_mode,
    get_simulated_mode,
    generate_state_for_directory,
    init_project_state
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_file(temp_dir):
    """Create a sample file in the temporary directory."""
    file_path = Path(temp_dir) / "test_file.txt"
    file_path.write_text("Hello, World!")
    return str(file_path)


@pytest.fixture
def sample_state_file(temp_dir):
    """Create a sample state.yaml file."""
    state_path = Path(temp_dir) / "state.yaml"
    state = {
        "version": "1.0",
        "simulated_mode": False,
        "artifacts": {
            "test_artifact": {
                "path": "test.txt",
                "hash": "abc123"
            }
        }
    }
    with open(state_path, "w") as f:
        yaml.safe_dump(state, f)
    return str(state_path)


def test_calculate_file_hash(sample_file):
    """Test that file hash calculation works correctly."""
    hash1 = calculate_file_hash(sample_file)
    hash2 = calculate_file_hash(sample_file)
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex length


def test_calculate_file_hash_nonexistent():
    """Test that FileNotFoundError is raised for missing files."""
    with pytest.raises(FileNotFoundError):
        calculate_file_hash("nonexistent_file.txt")


def test_calculate_directory_hash(temp_dir):
    """Test directory hash calculation."""
    # Create some files
    Path(temp_dir, "file1.txt").write_text("data1")
    Path(temp_dir, "file2.txt").write_text("data2")
    Path(temp_dir, "subdir").mkdir()
    Path(temp_dir, "subdir", "file3.txt").write_text("data3")

    hashes = calculate_directory_hash(temp_dir)

    assert "file1.txt" in hashes
    assert "file2.txt" in hashes
    assert "subdir/file3.txt" in hashes
    assert len(hashes) == 3


def test_load_state_yaml_existing(sample_state_file):
    """Test loading an existing state file."""
    state = load_state_yaml(sample_state_file)
    assert state["version"] == "1.0"
    assert state["simulated_mode"] is False
    assert "test_artifact" in state["artifacts"]


def test_load_state_yaml_nonexistent(temp_dir):
    """Test loading a non-existent state file initializes defaults."""
    state_path = Path(temp_dir) / "missing.yaml"
    state = load_state_yaml(str(state_path))
    assert state["version"] == "1.0"
    assert state["simulated_mode"] is False
    assert state["artifacts"] == {}


def test_save_and_load_state_yaml(temp_dir):
    """Test saving and reloading state."""
    state_path = Path(temp_dir) / "new_state.yaml"
    state = {
        "version": "2.0",
        "simulated_mode": True,
        "artifacts": {"new_art": {"path": "new.txt", "hash": "xyz"}}
    }

    save_state_yaml(str(state_path), state)
    assert state_path.exists()

    loaded = load_state_yaml(str(state_path))
    assert loaded["version"] == "2.0"
    assert loaded["simulated_mode"] is True
    assert "new_art" in loaded["artifacts"]


def test_update_artifact_hash(sample_file, temp_dir):
    """Test updating an artifact hash in state."""
    state_path = Path(temp_dir) / "state.yaml"
    # Initialize empty state
    save_state_yaml(str(state_path), {"artifacts": {}, "simulated_mode": False, "version": "1.0"})

    update_artifact_hash(str(state_path), "my_artifact", sample_file)

    state = load_state_yaml(str(state_path))
    assert "my_artifact" in state["artifacts"]
    assert state["artifacts"]["my_artifact"]["hash"] == calculate_file_hash(sample_file)


def test_set_and_get_simulated_mode(temp_dir):
    """Test setting and getting simulated mode flag."""
    state_path = Path(temp_dir) / "state.yaml"
    save_state_yaml(str(state_path), {"artifacts": {}, "simulated_mode": False, "version": "1.0"})

    set_simulated_mode(str(state_path), True)
    assert get_simulated_mode(str(state_path)) is True

    set_simulated_mode(str(state_path), False)
    assert get_simulated_mode(str(state_path)) is False


def test_generate_state_for_directory(temp_dir):
    """Test generating state for a directory of files."""
    # Create files
    Path(temp_dir, "a.txt").write_text("1")
    Path(temp_dir, "b.txt").write_text("2")

    state_path = Path(temp_dir) / "state.yaml"
    save_state_yaml(str(state_path), {"artifacts": {}, "simulated_mode": False, "version": "1.0"})

    generate_state_for_directory(temp_dir, str(state_path), "test_dir")

    state = load_state_yaml(str(state_path))
    assert "test_dir/a.txt" in state["artifacts"]
    assert "test_dir/b.txt" in state["artifacts"]


def test_init_project_state(temp_dir):
    """Test initializing a new project state file."""
    state_path = Path(temp_dir) / "state.yaml"
    # Ensure it doesn't exist
    if state_path.exists():
        state_path.unlink()

    # Mock get_path to return our temp path
    import code.utils.state_manager as sm
    original_get_path = sm.get_path
    sm.get_path = lambda x: str(Path(temp_dir) / x)

    try:
        init_project_state()
        assert state_path.exists()
        state = load_state_yaml(str(state_path))
        assert state["version"] == "1.0"
        assert state["simulated_mode"] is False
    finally:
        sm.get_path = original_get_path
