import os
import tempfile
from pathlib import Path
import pytest
import yaml

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
import sys
sys.path.insert(0, str(project_root))

from code.utils.versioning import hash_file, update_state_file


def test_hash_file_basic():
    """Test that hash_file computes a valid SHA-256 hash."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello, World!")
        temp_path = f.name

    try:
        hash_result = hash_file(temp_path)
        # SHA-256 hex digest is 64 characters long
        assert len(hash_result) == 64
        assert all(c in '0123456789abcdef' for c in hash_result)
    finally:
        os.unlink(temp_path)


def test_hash_file_nonexistent():
    """Test that hash_file raises FileNotFoundError for missing files."""
    with pytest.raises(FileNotFoundError):
        hash_file("/nonexistent/path/file.txt")


def test_hash_file_consistency():
    """Test that hashing the same file twice yields the same result."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Consistency Check")
        temp_path = f.name

    try:
        hash1 = hash_file(temp_path)
        hash2 = hash_file(temp_path)
        assert hash1 == hash2
    finally:
        os.unlink(temp_path)


def test_update_state_file_creates_yaml():
    """Test that update_state_file creates a valid YAML state file."""
    # We run this in the actual project context
    # The function should create the state directory and file
    update_state_file()
    
    # Verify the file was created
    state_file_path = project_root / "state" / "projects" / "PROJ-518-investigating-the-relationship-between-b.yaml"
    assert state_file_path.exists(), "State file was not created"
    
    # Verify it is valid YAML and contains expected keys
    with open(state_file_path, 'r') as f:
        content = yaml.safe_load(f)
    
    assert "project_id" in content
    assert content["project_id"] == "PROJ-518-investigating-the-relationship-between-b"
    assert "files" in content
    assert isinstance(content["files"], dict)
    
    # Clean up after test
    state_file_path.unlink()
    state_file_path.parent.rmdir()
    state_file_path.parent.parent.rmdir()