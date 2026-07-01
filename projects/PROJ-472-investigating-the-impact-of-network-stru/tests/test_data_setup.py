"""
Tests for data directory setup and checksum tracking.
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# We will mock the data root for testing to avoid polluting the real project structure
# by temporarily changing the working directory or mocking the function.
# However, since the code uses relative paths based on "data", we'll run these
# in a temporary directory structure that mimics the project layout.

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary project root with data directory structure."""
    # Create the structure
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Create subdirectories
    (data_dir / "raw").mkdir()
    (data_dir / "processed").mkdir()
    (data_dir / "results").mkdir()
    
    # Create a test file
    test_file = data_dir / "raw" / "test_file.txt"
    test_file.write_text("test content")
    
    # Change to the temp directory to make relative paths work
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    yield tmp_path
    
    # Restore original working directory
    os.chdir(original_cwd)


def test_ensure_data_directories_creates_missing(temp_project_root):
    """Test that ensure_data_directories creates missing directories."""
    import sys
    sys.path.insert(0, str(temp_project_root / ".."))
    from code.utils.data_setup import ensure_data_directories, get_data_root
    
    # Remove one directory
    target_dir = get_data_root() / "new_dir"
    if target_dir.exists():
        shutil.rmtree(target_dir)
        
    # Ensure it gets created
    created = ensure_data_directories()
    assert target_dir in created
    assert target_dir.exists()


def test_compute_file_checksum(temp_project_root):
    """Test checksum computation."""
    import sys
    sys.path.insert(0, str(temp_project_root / ".."))
    from code.utils.data_setup import compute_file_checksum, get_data_root
    
    test_file = get_data_root() / "raw" / "test_file.txt"
    checksum = compute_file_checksum(test_file)
    
    # SHA256 of "test content"
    expected = "d8e8fca2dc0f896fd7cb4cb0031ba249b7b15717495474219078218728497809" # This is actually incorrect, let's calculate properly
    # Correct SHA256 for "test content":
    import hashlib
    correct_hash = hashlib.sha256(b"test content").hexdigest()
    
    assert checksum == correct_hash


def test_load_and_save_checksums(temp_project_root):
    """Test loading and saving checksums."""
    import sys
    sys.path.insert(0, str(temp_project_root / ".."))
    from code.utils.data_setup import load_checksums, save_checksums, get_data_root
    
    # Test empty load
    checksums = load_checksums()
    assert checksums == {}
    
    # Save some checksums
    test_data = {"raw/test.txt": "abc123"}
    save_checksums(test_data)
    
    # Load and verify
    loaded = load_checksums()
    assert loaded == test_data
    
    # Verify file exists
    checksum_file = get_data_root() / "checksums.json"
    assert checksum_file.exists()


def test_update_checksum_for_file(temp_project_root):
    """Test updating checksum for a specific file."""
    import sys
    sys.path.insert(0, str(temp_project_root / ".."))
    from code.utils.data_setup import update_checksum_for_file, load_checksums, get_data_root
    
    test_file = get_data_root() / "raw" / "test_file.txt"
    update_checksum_for_file(test_file)
    
    checksums = load_checksums()
    assert "raw/test_file.txt" in checksums
    assert checksums["raw/test_file.txt"] != ""


def test_verify_file_integrity(temp_project_root):
    """Test file integrity verification."""
    import sys
    sys.path.insert(0, str(temp_project_root / ".."))
    from code.utils.data_setup import update_checksum_for_file, verify_file_integrity, get_data_root
    
    test_file = get_data_root() / "raw" / "test_file.txt"
    
    # Initially no checksum stored
    assert not verify_file_integrity(test_file)
    
    # Store checksum
    update_checksum_for_file(test_file)
    assert verify_file_integrity(test_file)
    
    # Modify file
    test_file.write_text("modified content")
    assert not verify_file_integrity(test_file)
    
    # Restore and verify again
    test_file.write_text("test content")
    assert verify_file_integrity(test_file)


def test_setup_data_environment(temp_project_root):
    """Test the main setup function."""
    import sys
    sys.path.insert(0, str(temp_project_root / ".."))
    from code.utils.data_setup import setup_data_environment, get_data_root
    
    # Remove checksum file to test initialization
    checksum_file = get_data_root() / "checksums.json"
    if checksum_file.exists():
        checksum_file.unlink()
        
    result = setup_data_environment()
    
    assert result["status"] == "success"
    assert "directories_created" in result
    assert "checksum_file" in result
    assert checksum_file.exists()
    
    # Verify checksum file is valid JSON
    with open(checksum_file, "r") as f:
        data = json.load(f)
        assert isinstance(data, dict)
