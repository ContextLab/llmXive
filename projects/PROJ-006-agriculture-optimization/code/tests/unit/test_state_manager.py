"""
Unit tests for src.utils.state_manager module.
"""

import os
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# We need to import the module under test.
# Since the project structure is code/src/, we adjust sys.path if necessary.
# However, standard pytest execution from root usually handles relative imports if configured.
# For safety in this snippet, we assume the environment is set up correctly or use relative import logic.
import sys
from pathlib import Path

# Add the 'code' directory to the path to allow imports from 'src'
code_root = Path(__file__).resolve().parent.parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.utils import state_manager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)


@pytest.fixture
def sample_file(temp_dir):
    """Create a sample file in the temporary directory."""
    file_path = temp_dir / "test_file.txt"
    file_path.write_text("Hello, World!")
    return file_path


def test_compute_file_hash(sample_file):
    """Test that compute_file_hash returns the correct SHA-256 hash."""
    expected_hash = hashlib.sha256(b"Hello, World!").hexdigest()
    actual_hash = state_manager.compute_file_hash(sample_file)
    assert actual_hash == expected_hash


def test_compute_file_hash_missing(temp_dir):
    """Test that compute_file_hash raises FileNotFoundError for missing files."""
    missing_file = temp_dir / "nonexistent.txt"
    with pytest.raises(FileNotFoundError):
        state_manager.compute_file_hash(missing_file)


def test_scan_directory_for_artifacts(temp_dir):
    """Test scanning a directory for artifacts."""
    # Create some files
    (temp_dir / "file1.txt").write_text("data1")
    (temp_dir / "file2.txt").write_text("data2")
    (temp_dir / ".hidden").write_text("hidden") # Should be skipped
    (temp_dir / "subdir").mkdir()
    (temp_dir / "subdir" / "file3.txt").write_text("data3")

    artifacts = state_manager.scan_directory_for_artifacts(temp_dir)
    filenames = [p.name for p in artifacts]

    assert "file1.txt" in filenames
    assert "file2.txt" in filenames
    assert "file3.txt" in filenames
    assert ".hidden" not in filenames


def test_scan_directory_nonexistent(temp_dir):
    """Test scanning a non-existent directory returns empty list."""
    result = state_manager.scan_directory_for_artifacts(temp_dir / "does_not_exist")
    assert result == []


def test_load_state_missing_file(temp_dir, monkeypatch):
    """Test loading state when the file does not exist."""
    # Mock the STATE_FILE path to point to a non-existent file in temp_dir
    fake_state_file = temp_dir / "missing_state.yaml"
    monkeypatch.setattr(state_manager, "STATE_FILE", fake_state_file)

    state = state_manager.load_state()

    assert state["project_id"] == "PROJ-006-agriculture-optimization"
    assert state["artifacts"] == {}


def test_save_state_and_load(temp_dir, monkeypatch):
    """Test saving and then loading the state."""
    fake_state_file = temp_dir / "test_state.yaml"
    monkeypatch.setattr(state_manager, "STATE_FILE", fake_state_file)

    test_state = {
        "project_id": "PROJ-006-agriculture-optimization",
        "last_updated": "2023-01-01",
        "artifacts": {"data/test.csv": "abc123"}
    }

    state_manager.save_state(test_state)

    # Verify file exists
    assert fake_state_file.exists()

    # Load it back
    loaded_state = state_manager.load_state()

    assert loaded_state["project_id"] == test_state["project_id"]
    assert loaded_state["artifacts"] == test_state["artifacts"]


def test_update_artifact_hashes_integration(temp_dir, monkeypatch, caplog):
    """Test the full update_artifact_hashes flow with mocked paths."""
    # Create a fake data directory structure
    data_raw = temp_dir / "data" / "raw"
    data_raw.mkdir(parents=True)
    test_file = data_raw / "sample.csv"
    test_file.write_text("col1,col2\n1,2")

    # Mock the module constants
    monkeypatch.setattr(state_manager, "PROJECT_ROOT", temp_dir)
    monkeypatch.setattr(state_manager, "STATE_DIR", temp_dir / "state" / "projects")
    monkeypatch.setattr(state_manager, "STATE_FILE", temp_dir / "state" / "projects" / "PROJ-006-agriculture-optimization.yaml")
    monkeypatch.setattr(state_manager, "DATA_RAW_DIR", data_raw)
    monkeypatch.setattr(state_manager, "DATA_PROCESSED_DIR", temp_dir / "data" / "processed")

    # Run update
    hashes = state_manager.update_artifact_hashes()

    # Verify hash was computed and stored
    assert len(hashes) == 1
    expected_rel_path = str(test_file.relative_to(temp_dir))
    assert expected_rel_path in hashes

    # Verify state file was created and updated
    state = state_manager.load_state()
    assert state["artifacts"][expected_rel_path] == hashes[expected_rel_path]


def test_verify_artifacts(temp_dir, monkeypatch):
    """Test verifying artifacts against stored state."""
    # Setup
    data_raw = temp_dir / "data" / "raw"
    data_raw.mkdir(parents=True)
    test_file = data_raw / "valid.csv"
    test_content = "valid"
    test_file.write_text(test_content)
    correct_hash = hashlib.sha256(test_content.encode()).hexdigest()

    # Mock paths
    monkeypatch.setattr(state_manager, "PROJECT_ROOT", temp_dir)
    monkeypatch.setattr(state_manager, "STATE_DIR", temp_dir / "state" / "projects")
    monkeypatch.setattr(state_manager, "STATE_FILE", temp_dir / "state" / "projects" / "PROJ-006-agriculture-optimization.yaml")
    monkeypatch.setattr(state_manager, "DATA_RAW_DIR", data_raw)
    monkeypatch.setattr(state_manager, "DATA_PROCESSED_DIR", temp_dir / "data" / "processed")

    # Save a state with the correct hash
    initial_state = {
        "project_id": "PROJ-006-agriculture-optimization",
        "artifacts": {str(test_file.relative_to(temp_dir)): correct_hash}
    }
    state_manager.save_state(initial_state)

    # Verify
    assert state_manager.verify_artifacts() is True

    # Corrupt the file
    test_file.write_text("invalid")
    assert state_manager.verify_artifacts() is False

    # Remove the file
    test_file.unlink()
    assert state_manager.verify_artifacts() is False
