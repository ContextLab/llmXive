import os
import tempfile
import pytest
from pathlib import Path
import hashlib
import yaml
import json

# Import functions to test
from downloaders import (
    calculate_sha256,
    generate_checksum_file,
    verify_checksum,
    update_state_file,
    DataFetchError
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def sample_file(temp_dir):
    """Create a sample file for testing."""
    file_path = Path(temp_dir) / "test_file.txt"
    content = "This is a test file for checksum verification."
    with open(file_path, 'w') as f:
        f.write(content)
    return file_path, content

def test_calculate_sha256(sample_file):
    """Test SHA-256 calculation."""
    file_path, _ = sample_file
    hash_result = calculate_sha256(str(file_path))
    
    # Calculate expected hash manually
    expected_hash = hashlib.sha256(b"This is a test file for checksum verification.").hexdigest()
    
    assert hash_result == expected_hash
    assert len(hash_result) == 64  # SHA-256 hex length

def test_calculate_sha256_file_not_found():
    """Test SHA-256 calculation with non-existent file."""
    with pytest.raises(FileNotFoundError):
        calculate_sha256("/non/existent/file.txt")

def test_generate_checksum_file(temp_dir):
    """Test checksum file generation."""
    file_path = Path(temp_dir) / "test.txt"
    content = "Test content"
    with open(file_path, 'w') as f:
        f.write(content)
    
    checksum_path = Path(temp_dir) / "test.txt.sha256"
    generate_checksum_file(str(file_path), str(checksum_path))
    
    # Verify file exists
    assert checksum_path.exists()
    
    # Verify content format
    with open(checksum_path, 'r') as f:
        content = f.read().strip()
        parts = content.split('  ')
        assert len(parts) == 2
        assert len(parts[0]) == 64  # Hash length
        assert parts[1] == "test.txt"

def test_verify_checksum_success(sample_file):
    """Test checksum verification with matching hash."""
    file_path, content = sample_file
    expected_hash = hashlib.sha256(content.encode()).hexdigest()
    
    assert verify_checksum(str(file_path), expected_hash) is True

def test_verify_checksum_failure(sample_file):
    """Test checksum verification with mismatched hash."""
    file_path, _ = sample_file
    wrong_hash = "a" * 64
    
    assert verify_checksum(str(file_path), wrong_hash) is False

def test_update_state_file(temp_dir):
    """Test state file update with checksums."""
    state_path = Path(temp_dir) / "state.yaml"
    
    # Create initial state with correct structure
    initial_state = {
        "artifact_hashes": {
            "existing.txt": "existing_hash"
        }
    }
    
    with open(state_path, 'w') as f:
        yaml.dump(initial_state, f)
    
    # Update with new checksums
    new_checksums = {
        "new.txt": "new_hash"
    }
    
    update_state_file(new_checksums, str(state_path))
    
    # Verify state file
    with open(state_path, 'r') as f:
        updated_state = yaml.safe_load(f)
    
    assert "artifact_hashes" in updated_state
    assert updated_state["artifact_hashes"]["existing.txt"] == "existing_hash"
    assert updated_state["artifact_hashes"]["new.txt"] == "new_hash"

def test_update_state_file_missing_key(temp_dir):
    """Test state file update when 'artifact_hashes' key is missing."""
    state_path = Path(temp_dir) / "state.yaml"
    
    # Create state without artifact_hashes
    with open(state_path, 'w') as f:
        yaml.dump({"some_key": "value"}, f)
    
    with pytest.raises(ValueError, match="missing 'artifact_hashes' key"):
        update_state_file({"test.txt": "hash"}, str(state_path))

def test_update_state_file_invalid_structure(temp_dir):
    """Test state file update when 'artifact_hashes' is not a dict."""
    state_path = Path(temp_dir) / "state.yaml"
    
    # Create state with artifact_hashes as a list
    with open(state_path, 'w') as f:
        yaml.dump({"artifact_hashes": ["list", "not", "dict"]}, f)
    
    with pytest.raises(ValueError, match="must be a dictionary"):
        update_state_file({"test.txt": "hash"}, str(state_path))

def test_generate_checksum_file_nonexistent():
    """Test checksum generation for non-existent file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "nonexistent.txt"
        checksum_path = Path(tmpdir) / "nonexistent.txt.sha256"
        
        with pytest.raises(FileNotFoundError):
            generate_checksum_file(str(file_path), str(checksum_path))