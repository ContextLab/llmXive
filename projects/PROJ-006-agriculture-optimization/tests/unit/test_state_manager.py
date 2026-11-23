import os
import tempfile
import shutil
from pathlib import Path
import pytest
import yaml
import hashlib

from src.utils import state_manager

@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for testing."""
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    
    # Create necessary directories
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    Path("state/projects").mkdir(parents=True, exist_ok=True)
    
    yield temp_dir
    
    # Cleanup
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)

def test_compute_file_hash(temp_workspace):
    """Test hash computation on a known file."""
    test_file = Path("data/raw/test.txt")
    content = "Hello, World!"
    test_file.write_text(content)
    
    expected_hash = hashlib.sha256(content.encode()).hexdigest()
    actual_hash = state_manager.compute_file_hash(test_file)
    
    assert actual_hash == expected_hash

def test_compute_file_hash_not_found(temp_workspace):
    """Test hash computation on a missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        state_manager.compute_file_hash(Path("nonexistent.txt"))

def test_scan_directory_for_artifacts(temp_workspace):
    """Test directory scanning."""
    # Create test files
    Path("data/raw/file1.txt").write_text("a")
    Path("data/raw/file2.txt").write_text("b")
    Path("data/processed/file3.txt").write_text("c")
    
    raw_files = state_manager.scan_directory_for_artifacts(Path("data/raw"))
    processed_files = state_manager.scan_directory_for_artifacts(Path("data/processed"))
    
    assert len(raw_files) == 2
    assert len(processed_files) == 1
    assert all(f.exists() for f in raw_files + processed_files)

def test_load_state_initializes_empty(temp_workspace):
    """Test that load_state initializes structure if file missing."""
    state = state_manager.load_state(Path("state/projects/PROJ-006-agriculture-optimization.yaml"))
    
    assert "project_id" in state
    assert "artifact_hashes" in state
    assert "data_raw" in state["artifact_hashes"]
    assert "data_processed" in state["artifact_hashes"]

def test_update_artifact_hashes(temp_workspace):
    """Test updating artifact hashes."""
    # Create test files
    Path("data/raw/test1.txt").write_text("content1")
    Path("data/processed/test2.txt").write_text("content2")
    
    state = state_manager.load_state(Path("state/projects/PROJ-006-agriculture-optimization.yaml"))
    state = state_manager.update_artifact_hashes(state)
    
    assert "test1.txt" in state["artifact_hashes"]["data_raw"]
    assert "test2.txt" in state["artifact_hashes"]["data_processed"]
    
    # Verify hashes are correct
    hash1 = state_manager.compute_file_hash(Path("data/raw/test1.txt"))
    assert state["artifact_hashes"]["data_raw"]["test1.txt"] == hash1

def test_save_and_load_state(temp_workspace):
    """Test saving and loading state."""
    state = {
        "project_id": "TEST",
        "artifact_hashes": {
            "data_raw": {"test.txt": "abc123"},
            "data_processed": {}
        }
    }
    state_path = Path("state/projects/PROJ-006-agriculture-optimization.yaml")
    
    state_manager.save_state(state, state_path)
    
    loaded_state = state_manager.load_state(state_path)
    
    assert loaded_state["project_id"] == "TEST"
    assert loaded_state["artifact_hashes"]["data_raw"]["test.txt"] == "abc123"

def test_verify_artifacts_success(temp_workspace):
    """Test artifact verification when all files match."""
    Path("data/raw/verify.txt").write_text("verify_content")
    
    state = {
        "project_id": "TEST",
        "artifact_hashes": {
            "data_raw": {"verify.txt": state_manager.compute_file_hash(Path("data/raw/verify.txt"))},
            "data_processed": {}
        }
    }
    
    assert state_manager.verify_artifacts(state) is True

def test_verify_artifacts_missing_file(temp_workspace):
    """Test artifact verification when a file is missing."""
    state = {
        "project_id": "TEST",
        "artifact_hashes": {
            "data_raw": {"missing.txt": "abc123"},
            "data_processed": {}
        }
    }
    
    assert state_manager.verify_artifacts(state) is False

def test_verify_artifacts_hash_mismatch(temp_workspace):
    """Test artifact verification when hash doesn't match."""
    Path("data/raw/mismatch.txt").write_text("new_content")
    
    state = {
        "project_id": "TEST",
        "artifact_hashes": {
            "data_raw": {"mismatch.txt": "old_hash"},
            "data_processed": {}
        }
    }
    
    assert state_manager.verify_artifacts(state) is False

def test_main_function(temp_workspace):
    """Test the main CLI function."""
    # Create a dummy file
    Path("data/raw/main_test.txt").write_text("main_test_content")
    
    result = state_manager.main()
    
    assert result == 0
    assert Path("state/projects/PROJ-006-agriculture-optimization.yaml").exists()