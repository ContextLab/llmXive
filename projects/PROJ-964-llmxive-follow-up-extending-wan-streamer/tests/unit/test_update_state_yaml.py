"""
Unit tests for update_state_yaml.py
"""

import os
import tempfile
from pathlib import Path
import yaml
import pytest

# Import the module functions
# We need to add the parent directory to the path to import code.utils
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from utils.update_state_yaml import (
    compute_file_hash,
    load_state_yaml,
    save_state_yaml,
    update_state_with_artifacts,
    get_file_size_mb
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_file(temp_dir):
    """Create a sample file for testing."""
    file_path = temp_dir / "test.txt"
    file_path.write_text("Hello, World!")
    return file_path

def test_compute_file_hash(sample_file):
    """Test that compute_file_hash returns a valid hex string."""
    file_hash = compute_file_hash(sample_file)
    assert len(file_hash) == 64  # SHA256 hex length
    assert file_hash.islower()
    assert all(c in '0123456789abcdef' for c in file_hash)

def test_compute_file_hash_missing_file(temp_dir):
    """Test that compute_file_hash raises FileNotFoundError for missing file."""
    missing_file = temp_dir / "nonexistent.txt"
    with pytest.raises(FileNotFoundError):
        compute_file_hash(missing_file)

def test_get_file_size_mb(sample_file):
    """Test file size calculation."""
    size = get_file_size_mb(sample_file)
    # "Hello, World!" is 13 bytes
    assert 0 < size < 1

def test_load_state_yaml_new(temp_dir):
    """Test loading a non-existent state file creates a default structure."""
    state_path = temp_dir / "state.yaml"
    state = load_state_yaml(state_path)
    assert "project_id" in state
    assert "artifacts" in state
    assert state["artifacts"] == {}

def test_load_state_yaml_existing(temp_dir, sample_file):
    """Test loading an existing state file."""
    state_path = temp_dir / "state.yaml"
    initial_state = {"project_id": "TEST-001", "artifacts": {"old.txt": {"hash": "abc"}}}
    with open(state_path, "w") as f:
        yaml.dump(initial_state, f)

    state = load_state_yaml(state_path)
    assert state["project_id"] == "TEST-001"
    assert "old.txt" in state["artifacts"]

def test_save_state_yaml(temp_dir):
    """Test saving state to YAML."""
    state_path = temp_dir / "state.yaml"
    state = {"project_id": "TEST-002", "artifacts": {"key": "value"}, "last_updated": "2023-01-01"}
    save_state_yaml(state, state_path)
    assert state_path.exists()
    with open(state_path, "r") as f:
        loaded = yaml.safe_load(f)
    assert loaded["project_id"] == "TEST-002"

def test_update_state_with_artifacts(temp_dir, sample_file):
    """Test updating state with artifact metadata."""
    state_path = temp_dir / "state.yaml"
    state = load_state_yaml(state_path)
    base_path = temp_dir

    update_state_with_artifacts(state, [sample_file], base_path)

    # Check that the artifact was added
    assert len(state["artifacts"]) == 1
    artifact_key = "test.txt"  # Relative path
    assert artifact_key in state["artifacts"]

    entry = state["artifacts"][artifact_key]
    assert "hash" in entry
    assert "size_mb" in entry
    assert entry["path"] == artifact_key