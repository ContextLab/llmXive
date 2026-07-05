import os
import yaml
import tempfile
import shutil
import pytest

from code.artifact_manager import (
    ensure_state_dir,
    load_artifact_hashes,
    save_artifact_hashes,
    update_artifact_hash,
    verify_artifact_integrity,
    STATE_DIR,
    ARTIFACT_HASHES_FILE
)

@pytest.fixture
def mock_state_dir():
    """Create a temporary directory to act as the state directory for testing."""
    original_state_dir = STATE_DIR
    temp_dir = tempfile.mkdtemp()
    # We need to monkeypatch the module's global variables to use the temp dir
    import code.artifact_manager as am
    am.STATE_DIR = temp_dir
    am.ARTIFACT_HASHES_FILE = os.path.join(temp_dir, "artifact_hashes.yaml")
    yield temp_dir
    # Cleanup
    am.STATE_DIR = original_state_dir
    am.ARTIFACT_HASHES_FILE = "state/artifact_hashes.yaml"
    shutil.rmtree(temp_dir)

def test_ensure_state_dir_creates_directory(mock_state_dir):
    """Test that ensure_state_dir creates the directory if it doesn't exist."""
    # The fixture sets up the dir, but let's verify the function works
    result = ensure_state_dir()
    assert os.path.isdir(result)
    assert result == mock_state_dir

def test_load_artifact_hashes_empty(mock_state_dir):
    """Test loading hashes when file doesn't exist."""
    hashes = load_artifact_hashes()
    assert isinstance(hashes, dict)
    assert len(hashes) == 0

def test_save_artifact_hashes(mock_state_dir):
    """Test saving hashes to file."""
    test_data = {"data/file1.txt": "abc123", "data/file2.txt": "def456"}
    save_artifact_hashes(test_data)

    # Verify file exists
    assert os.path.exists(ARTIFACT_HASHES_FILE)

    # Verify content
    with open(ARTIFACT_HASHES_FILE, 'r') as f:
        loaded = yaml.safe_load(f)
    
    assert "artifacts" in loaded
    assert loaded["artifacts"] == test_data

def test_update_artifact_hash(mock_state_dir):
    """Test updating a specific artifact hash."""
    # Initial save
    save_artifact_hashes({"file1.txt": "hash1"})
    
    # Update
    update_artifact_hash("file2.txt", "hash2")
    
    # Verify both exist
    hashes = load_artifact_hashes()
    assert hashes["file1.txt"] == "hash1"
    assert hashes["file2.txt"] == "hash2"

def test_verify_artifact_integrity_match(mock_state_dir):
    """Test verification when hashes match."""
    save_artifact_hashes({"file.txt": "correct_hash"})
    assert verify_artifact_integrity("file.txt", "correct_hash") is True

def test_verify_artifact_integrity_mismatch(mock_state_dir):
    """Test verification when hashes don't match."""
    save_artifact_hashes({"file.txt": "correct_hash"})
    assert verify_artifact_integrity("file.txt", "wrong_hash") is False

def test_verify_artifact_integrity_missing(mock_state_dir):
    """Test verification for a non-existent artifact."""
    save_artifact_hashes({"file.txt": "hash"})
    assert verify_artifact_integrity("missing.txt", "hash") is False
