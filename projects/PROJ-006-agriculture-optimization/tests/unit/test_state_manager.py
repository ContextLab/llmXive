import os
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

import sys
# Add code to path if running from tests/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

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
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_file(temp_dir):
    file_path = temp_dir / "test.txt"
    file_path.write_text("Hello World")
    return file_path

def test_compute_file_hash(sample_file):
    hash1 = compute_file_hash(sample_file)
    hash2 = compute_file_hash(sample_file)
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 hex length

def test_compute_file_hash_missing(temp_dir):
    missing_file = temp_dir / "nonexistent.txt"
    with pytest.raises(FileNotFoundError):
        compute_file_hash(missing_file)

def test_scan_directory_for_artifacts(temp_dir):
    # Create structure
    (temp_dir / "subdir").mkdir()
    (temp_dir / "file1.txt").write_text("a")
    (temp_dir / "subdir" / "file2.txt").write_text("b")
    (temp_dir / ".hidden").write_text("c")

    files = scan_directory_for_artifacts(temp_dir)
    paths = [f.name for f in files]
    
    assert "file1.txt" in paths
    assert "file2.txt" in paths
    assert ".hidden" not in paths
    assert len(files) == 2

def test_scan_directory_nonexistent(temp_dir):
    non_existent = temp_dir / "does_not_exist"
    files = scan_directory_for_artifacts(non_existent)
    assert files == []

def test_load_state_missing_file(temp_dir):
    state_path = temp_dir / "state.yaml"
    state = load_state(state_path)
    assert state == {
        "project_id": "PROJ-006-agriculture-optimization",
        "artifact_hashes": {}
    }

def test_save_state_and_load(temp_dir):
    state_path = temp_dir / "state.yaml"
    test_state = {"project_id": "TEST", "artifact_hashes": {"key": "val"}}
    save_state(state_path, test_state)
    
    loaded = load_state(state_path)
    assert loaded == test_state

def test_update_artifact_hashes_integration(temp_dir):
    # Setup a mock project structure within temp_dir
    # We need to mock _PROJECT_ROOT or pass paths that work relative to temp_dir
    # Since update_artifact_hashes uses a global _PROJECT_ROOT, we patch it.
    
    data_dir = temp_dir / "data" / "raw"
    data_dir.mkdir(parents=True)
    test_file = data_dir / "test.txt"
    test_file.write_text("content")
    
    state_path = temp_dir / "state.yaml"
    
    # Patch the global project root to be temp_dir for this test
    with patch('src.utils.state_manager._PROJECT_ROOT', temp_dir):
        logger = MagicMock()
        update_artifact_hashes(state_path, [data_dir], logger)
        
        state = load_state(state_path)
        assert "artifact_hashes" in state
        assert "data/raw/test.txt" in state["artifact_hashes"]
        assert len(state["artifact_hashes"]) == 1

def test_verify_artifacts(temp_dir):
    data_dir = temp_dir / "data" / "raw"
    data_dir.mkdir(parents=True)
    test_file = data_dir / "test.txt"
    test_file.write_text("content")
    
    state_path = temp_dir / "state.yaml"
    
    # First, update state
    with patch('src.utils.state_manager._PROJECT_ROOT', temp_dir):
        logger = MagicMock()
        update_artifact_hashes(state_path, [data_dir], logger)
        
        # Verify should pass
        assert verify_artifacts(state_path, logger) is True

        # Modify file
        test_file.write_text("modified")
        assert verify_artifacts(state_path, logger) is False

        # Delete file
        test_file.unlink()
        assert verify_artifacts(state_path, logger) is False