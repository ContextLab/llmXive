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
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.utils import state_manager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_file(temp_dir):
    """Create a sample file for testing."""
    file_path = temp_dir / "test_file.txt"
    content = "Test content for hashing"
    file_path.write_text(content)
    return file_path


def test_compute_file_hash(sample_file):
    """Test that file hash is computed correctly."""
    expected_hash = hashlib.sha256(b"Test content for hashing").hexdigest()
    actual_hash = state_manager.compute_file_hash(sample_file)
    assert actual_hash == expected_hash


def test_compute_file_hash_missing():
    """Test that None is returned for missing files."""
    missing_path = Path("/nonexistent/file.txt")
    result = state_manager.compute_file_hash(missing_path)
    assert result is None


def test_scan_directory_for_artifacts(temp_dir):
    """Test directory scanning for artifacts."""
    # Create test files
    (temp_dir / "file1.txt").write_text("content1")
    (temp_dir / "subdir").mkdir()
    (temp_dir / "subdir" / "file2.txt").write_text("content2")
    
    # Temporarily set PROJECT_ROOT to temp_dir for this test
    original_root = state_manager.PROJECT_ROOT
    state_manager.PROJECT_ROOT = temp_dir
    
    try:
        artifacts = state_manager.scan_directory_for_artifacts(temp_dir)
        
        # Should find 2 files (excluding the subdir itself)
        assert len(artifacts) == 2
        
        # Check that file1.txt is in artifacts
        assert any("file1.txt" in path for path in artifacts.keys())
        assert any("file2.txt" in path for path in artifacts.keys())
    finally:
        state_manager.PROJECT_ROOT = original_root


def test_scan_directory_nonexistent(temp_dir):
    """Test scanning a non-existent directory."""
    nonexistent_dir = temp_dir / "nonexistent"
    artifacts = state_manager.scan_directory_for_artifacts(nonexistent_dir)
    assert artifacts == {}


def test_load_state_missing_file(temp_dir):
    """Test loading state when file doesn't exist."""
    # Temporarily set STATE_FILE to a non-existent path
    original_state_file = state_manager.STATE_FILE
    state_manager.STATE_FILE = temp_dir / "nonexistent.yaml"
    
    try:
        state = state_manager.load_state()
        assert state == {
            "project_id": "PROJ-006-agriculture-optimization",
            "last_updated": None,
            "artifact_hashes": {}
        }
    finally:
        state_manager.STATE_FILE = original_state_file


def test_save_state_and_load(temp_dir):
    """Test saving and loading state."""
    test_state_file = temp_dir / "test_state.yaml"
    test_state = {
        "project_id": "TEST-PROJECT",
        "last_updated": "test",
        "artifact_hashes": {"file.txt": "abc123"}
    }
    
    # Temporarily set STATE_FILE
    original_state_file = state_manager.STATE_FILE
    state_manager.STATE_FILE = test_state_file
    
    try:
        # Save state
        success = state_manager.save_state(test_state)
        assert success
        
        # Verify file exists
        assert test_state_file.exists()
        
        # Load state
        loaded_state = state_manager.load_state()
        assert loaded_state == test_state
    finally:
        state_manager.STATE_FILE = original_state_file


def test_update_artifact_hashes_integration(temp_dir):
    """Test the full update_artifact_hashes workflow."""
    # Create a fake data directory structure
    fake_data_dir = temp_dir / "data"
    (fake_data_dir / "raw").mkdir(parents=True)
    (fake_data_dir / "processed").mkdir()
    
    # Add test files
    (fake_data_dir / "raw" / "test.csv").write_text("a,b\n1,2")
    (fake_data_dir / "processed" / "result.json").write_text('{"ok": true}')
    
    # Temporarily override paths
    original_data_dirs = state_manager.DATA_DIRS
    original_project_root = state_manager.PROJECT_ROOT
    original_state_file = state_manager.STATE_FILE
    
    state_manager.DATA_DIRS = [fake_data_dir / "raw", fake_data_dir / "processed"]
    state_manager.PROJECT_ROOT = temp_dir
    state_manager.STATE_FILE = temp_dir / "state.yaml"
    
    try:
        hashes = state_manager.update_artifact_hashes()
        
        # Should have found 2 files
        assert len(hashes) == 2
        
        # Verify state was saved
        assert state_manager.STATE_FILE.exists()
        
        # Verify state content
        with open(state_manager.STATE_FILE, "r") as f:
            saved_state = yaml.safe_load(f)
        
        assert saved_state["project_id"] == "PROJ-006-agriculture-optimization"
        assert len(saved_state["artifact_hashes"]) == 2
    finally:
        state_manager.DATA_DIRS = original_data_dirs
        state_manager.PROJECT_ROOT = original_project_root
        state_manager.STATE_FILE = original_state_file


def test_verify_artifacts(temp_dir):
    """Test artifact verification."""
    # Create test files and state
    test_state_file = temp_dir / "state.yaml"
    test_data_dir = temp_dir / "data"
    (test_data_dir / "test.txt").mkdir(parents=True)
    test_file = test_data_dir / "test.txt"
    test_file.write_text("content")
    
    file_hash = hashlib.sha256(b"content").hexdigest()
    
    test_state = {
        "project_id": "PROJ-006-agriculture-optimization",
        "last_updated": "test",
        "artifact_hashes": {"data/test.txt": file_hash}
    }
    
    # Temporarily override paths
    original_state_file = state_manager.STATE_FILE
    original_project_root = state_manager.PROJECT_ROOT
    
    state_manager.STATE_FILE = test_state_file
    state_manager.PROJECT_ROOT = temp_dir
    
    try:
        # Save state
        state_manager.save_state(test_state)
        
        # Verify should pass
        result = state_manager.verify_artifacts()
        assert result is True
        
        # Now corrupt the hash
        test_state["artifact_hashes"]["data/test.txt"] = "wrong_hash"
        state_manager.save_state(test_state)
        
        # Verify should fail
        result = state_manager.verify_artifacts()
        assert result is False
    finally:
        state_manager.STATE_FILE = original_state_file
        state_manager.PROJECT_ROOT = original_project_root