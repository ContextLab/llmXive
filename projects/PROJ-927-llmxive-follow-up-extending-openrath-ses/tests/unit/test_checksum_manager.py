"""Unit tests for the checksum_manager utility (T017a)."""
import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Import from the project structure
from utils.checksum_manager import calculate_sha256, scan_directory_for_files, update_artifact_hashes
from config import load_state, save_state, ensure_directories, STATE_DIR

@pytest.fixture
def temp_project_root():
    """Create a temporary directory structure mimicking the project."""
    root = tempfile.mkdtemp()
    # Ensure the state directory exists in temp
    state_dir = Path(root) / "state" / "projects"
    state_dir.mkdir(parents=True, exist_ok=True)
    # Create an initial empty state file
    state_file = state_dir / "PROJ-927-llmxive-follow-up-extending-openrath-ses.yaml"
    state_file.write_text("artifact_hashes: {}\n")
    
    # Create a mock data directory with files
    data_dir = Path(root) / "data" / "raw" / "workflows"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "file1.txt").write_text("content1")
    (data_dir / "file2.txt").write_text("content2")
    
    # Change to temp root to simulate project root context
    original_cwd = os.getcwd()
    os.chdir(root)
    yield root
    os.chdir(original_cwd)
    shutil.rmtree(root)

def test_calculate_sha256_file_exists(temp_project_root):
    """Test calculating SHA256 for an existing file."""
    file_path = Path(temp_project_root) / "data" / "raw" / "workflows" / "file1.txt"
    hash_val = calculate_sha256(str(file_path))
    assert isinstance(hash_val, str)
    assert len(hash_val) == 64  # SHA256 hex length
    assert all(c in '0123456789abcdef' for c in hash_val)

def test_calculate_sha256_file_not_exists(temp_project_root):
    """Test that calculating SHA256 for a missing file returns None or raises."""
    file_path = Path(temp_project_root) / "non_existent.txt"
    # The implementation should handle missing files gracefully or return None
    result = calculate_sha256(str(file_path))
    assert result is None

def test_scan_directory_for_files(temp_project_root):
    """Test scanning a directory for files."""
    data_dir = Path(temp_project_root) / "data" / "raw" / "workflows"
    files = scan_directory_for_files(str(data_dir))
    assert isinstance(files, list)
    assert len(files) == 2
    assert all(isinstance(f, str) for f in files)
    assert any("file1.txt" in f for f in files)
    assert any("file2.txt" in f for f in files)

def test_scan_directory_empty(temp_project_root):
    """Test scanning an empty directory."""
    empty_dir = Path(temp_project_root) / "data" / "empty"
    empty_dir.mkdir(parents=True, exist_ok=True)
    files = scan_directory_for_files(str(empty_dir))
    assert files == []

def test_update_artifact_hashes(temp_project_root):
    """Test updating the state file with calculated hashes."""
    data_dir = Path(temp_project_root) / "data" / "raw" / "workflows"
    # Load initial state
    state = load_state()
    initial_hashes = state.get("artifact_hashes", {})
    assert initial_hashes == {}

    # Update hashes
    update_artifact_hashes(str(data_dir))

    # Verify state was updated
    state_after = load_state()
    new_hashes = state_after.get("artifact_hashes", {})
    assert len(new_hashes) == 2
    # Verify keys are file paths (relative or absolute depending on impl)
    for path, hash_val in new_hashes.items():
        assert isinstance(path, str)
        assert isinstance(hash_val, str)
        assert len(hash_val) == 64

def test_update_artifact_hashes_persistence(temp_project_root):
    """Test that hashes are persisted to disk correctly."""
    data_dir = Path(temp_project_root) / "data" / "raw" / "workflows"
    update_artifact_hashes(str(data_dir))
    
    # Reload state from disk to ensure persistence
    state = load_state()
    assert "artifact_hashes" in state
    assert len(state["artifact_hashes"]) == 2
