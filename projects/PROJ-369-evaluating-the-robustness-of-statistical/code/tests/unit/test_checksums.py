import os
import tempfile
import hashlib
from pathlib import Path
import pytest
import yaml

from src.utils.checksums import (
    compute_file_checksum,
    compute_directory_checksum,
    load_state,
    save_state,
    update_checksums_for_project,
    validate_checksums_for_project
)
from src.utils.config import get_path

@pytest.fixture
def temp_test_dir(tmp_path):
    """Create a temporary directory with test files."""
    # Create some test files
    (tmp_path / "file1.txt").write_text("Hello, World!")
    (tmp_path / "file2.txt").write_text("Test data")
    
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "file3.txt").write_text("Nested file")
    
    return tmp_path

def test_compute_file_checksum():
    """Test SHA-256 checksum computation for a single file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Test content")
        temp_path = Path(f.name)
    
    try:
        checksum = compute_file_checksum(temp_path)
        # Verify it's a valid SHA-256 hash (64 hex characters)
        assert len(checksum) == 64
        assert all(c in '0123456789abcdef' for c in checksum)
        
        # Verify against known hash
        expected = hashlib.sha256(b"Test content").hexdigest()
        assert checksum == expected
    finally:
        os.unlink(temp_path)

def test_compute_directory_checksum(temp_test_dir):
    """Test checksum computation for a directory."""
    checksums = compute_directory_checksum(temp_test_dir)
    
    assert len(checksums) == 3  # file1.txt, file2.txt, subdir/file3.txt
    assert "file1.txt" in checksums
    assert "file2.txt" in checksums
    assert "subdir/file3.txt" in checksums

def test_save_and_load_state(tmp_path):
    """Test state serialization and deserialization."""
    test_state = {
        "project1": {
            "checksums": {
                "data/raw": {"files": {"test.txt": "abc123"}}
            }
        }
    }
    
    state_file = tmp_path / "test_state.yaml"
    save_state(state_file, test_state)
    
    loaded = load_state(state_file)
    assert loaded == test_state

def test_update_checksums_for_project(tmp_path, monkeypatch):
    """Test updating checksums for a project."""
    # Monkeypatch get_path to use temp directory
    original_get_path = get_path
    
    def mock_get_path(path_name):
        if path_name == "state":
            return tmp_path / "state"
        elif path_name == "data/raw":
            return tmp_path / "data/raw"
        elif path_name == "data/processed":
            return tmp_path / "data/processed"
        elif path_name == "results":
            return tmp_path / "results"
        return original_get_path(path_name)
    
    monkeypatch.setattr("src.utils.checksums.get_path", mock_get_path)
    monkeypatch.setattr("src.utils.directory_manager.get_path", mock_get_path)
    
    # Create test directories with files
    (tmp_path / "data/raw").mkdir(parents=True)
    (tmp_path / "data/raw" / "test.txt").write_text("Raw data")
    
    (tmp_path / "data/processed").mkdir(parents=True)
    (tmp_path / "results").mkdir(parents=True)
    
    # Update checksums
    update_checksums_for_project(
        "TEST-PROJECT",
        ["data/raw", "data/processed", "results"]
    )
    
    # Verify state file was created
    state_file = tmp_path / "state" / "projects" / "TEST-PROJECT.yaml"
    assert state_file.exists()
    
    # Verify content
    with open(state_file) as f:
        state = yaml.safe_load(f)
    
    assert "TEST-PROJECT" in state
    assert "checksums" in state["TEST-PROJECT"]
    assert "data/raw" in state["TEST-PROJECT"]["checksums"]
    assert "file1.txt" in state["TEST-PROJECT"]["checksums"]["data/raw"]["files"] or "test.txt" in state["TEST-PROJECT"]["checksums"]["data/raw"]["files"]

def test_validate_checksums(tmp_path, monkeypatch):
    """Test checksum validation."""
    original_get_path = get_path
    
    def mock_get_path(path_name):
        if path_name == "state":
            return tmp_path / "state"
        elif path_name == "data/raw":
            return tmp_path / "data/raw"
        elif path_name == "data/processed":
            return tmp_path / "data/processed"
        elif path_name == "results":
            return tmp_path / "results"
        return original_get_path(path_name)
    
    monkeypatch.setattr("src.utils.checksums.get_path", mock_get_path)
    
    # Setup directories and initial state
    (tmp_path / "data/raw").mkdir(parents=True)
    (tmp_path / "data/raw" / "test.txt").write_text("Raw data")
    (tmp_path / "data/processed").mkdir(parents=True)
    (tmp_path / "results").mkdir(parents=True)
    
    # Initialize checksums
    update_checksums_for_project(
        "TEST-PROJECT",
        ["data/raw", "data/processed", "results"]
    )
    
    # Validate - should pass
    results = validate_checksums_for_project(
        "TEST-PROJECT",
        ["data/raw", "data/processed", "results"]
    )
    assert all(results.values())
    
    # Modify a file - should fail
    (tmp_path / "data/raw" / "test.txt").write_text("Modified data")
    results = validate_checksums_for_project(
        "TEST-PROJECT",
        ["data/raw"]
    )
    assert results["data/raw"] == False
