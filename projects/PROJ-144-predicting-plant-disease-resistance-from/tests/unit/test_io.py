import os
import tempfile
import yaml
import pytest
from pathlib import Path

from code.utils.io import compute_file_hash, log_artifact
from code.utils.constants import STATE_DIR, ARTIFACT_HASHES_FILE

@pytest.fixture
def temp_file():
    """Create a temporary file with known content."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello, World!")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def clean_state():
    """Ensure a clean state file for testing."""
    # Remove existing state file if present
    if os.path.exists(ARTIFACT_HASHES_FILE):
        os.remove(ARTIFACT_HASHES_FILE)
    yield
    # Cleanup after test
    if os.path.exists(ARTIFACT_HASHES_FILE):
        os.remove(ARTIFACT_HASHES_FILE)

def test_compute_sha256_hash(temp_file):
    """Test SHA256 hash computation."""
    # Known SHA256 for "Hello, World!"
    expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
    result = compute_file_hash(temp_file, "sha256")
    assert result == expected_hash

def test_compute_md5_hash(temp_file):
    """Test MD5 hash computation."""
    # Known MD5 for "Hello, World!"
    expected_hash = "65a8e27d8879283831b664bd8b7f0ad4"
    result = compute_file_hash(temp_file, "md5")
    assert result == expected_hash

def test_compute_hash_invalid_algorithm(temp_file):
    """Test that invalid algorithm raises ValueError."""
    with pytest.raises(ValueError):
        compute_file_hash(temp_file, "invalid_algo")

def test_compute_hash_missing_file():
    """Test that missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        compute_file_hash("nonexistent_file.txt")

def test_log_artifact(clean_state, temp_file):
    """Test logging an artifact to the state file."""
    log_artifact(temp_file, description="Test artifact", metadata={"source": "test"})
    
    assert os.path.exists(ARTIFACT_HASHES_FILE)
    
    with open(ARTIFACT_HASHES_FILE, "r") as f:
        state = yaml.safe_load(f)
    
    artifact_key = os.path.basename(temp_file)
    assert artifact_key in state
    assert state[artifact_key]["hash"] == compute_file_hash(temp_file, "sha256")
    assert state[artifact_key]["description"] == "Test artifact"
    assert state[artifact_key]["metadata"]["source"] == "test"

def test_log_artifact_overwrites_existing(clean_state, temp_file):
    """Test that logging the same file twice overwrites the entry."""
    log_artifact(temp_file, description="First")
    log_artifact(temp_file, description="Updated")
    
    with open(ARTIFACT_HASHES_FILE, "r") as f:
        state = yaml.safe_load(f)
    
    artifact_key = os.path.basename(temp_file)
    assert state[artifact_key]["description"] == "Updated"

def test_log_artifact_missing_file(clean_state):
    """Test logging a missing file prints warning and does not crash."""
    # Should not raise, just print warning
    log_artifact("nonexistent_file.txt", description="Missing")
    
    # State file should not be created or updated with this entry
    if os.path.exists(ARTIFACT_HASHES_FILE):
        with open(ARTIFACT_HASHES_FILE, "r") as f:
            state = yaml.safe_load(f)
        assert "nonexistent_file.txt" not in state