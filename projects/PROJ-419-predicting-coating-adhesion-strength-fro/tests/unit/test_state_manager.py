"""
Unit tests for the state_manager module.

Tests checksum calculation, file scanning, and state file generation.
"""
import os
import tempfile
import yaml
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.state_manager import (
    calculate_file_checksum,
    scan_raw_data_directory,
    generate_state_checksums,
    write_state_file,
    verify_state_checksums,
    STATE_FILE,
    RAW_DATA_DIR,
    ALGORITHM
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create subdirectories
        subdir = os.path.join(tmpdir, "subdir")
        os.makedirs(subdir)
        
        # Create test files
        file1 = os.path.join(tmpdir, "test1.txt")
        with open(file1, 'w') as f:
            f.write("Hello, World!")
        
        file2 = os.path.join(subdir, "test2.txt")
        with open(file2, 'w') as f:
            f.write("Test content for checksum")
        
        yield tmpdir

@pytest.fixture
def mock_raw_dir(temp_dir):
    """Mock the RAW_DATA_DIR for testing."""
    original_dir = RAW_DATA_DIR
    # We can't easily mock the global constant, so we'll test with the temp_dir directly
    return temp_dir

def test_calculate_file_checksum():
    """Test checksum calculation for a known string."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = f.name
    
    try:
        checksum = calculate_file_checksum(temp_path)
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA256 hex length
        assert all(c in '0123456789abcdef' for c in checksum)
    finally:
        os.unlink(temp_path)

def test_calculate_file_checksum_nonexistent_file():
    """Test that FileNotFoundError is raised for missing files."""
    with pytest.raises(FileNotFoundError):
        calculate_file_checksum("nonexistent_file.txt")

def test_calculate_file_checksum_different_content():
    """Test that different content produces different checksums."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f1:
        f1.write("content 1")
        path1 = f1.name
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f2:
        f2.write("content 2")
        path2 = f2.name
    
    try:
        checksum1 = calculate_file_checksum(path1)
        checksum2 = calculate_file_checksum(path2)
        assert checksum1 != checksum2
    finally:
        os.unlink(path1)
        os.unlink(path2)

def test_scan_raw_data_directory(temp_dir):
    """Test scanning a directory for files."""
    files = scan_raw_data_directory(temp_dir)
    
    assert isinstance(files, list)
    assert len(files) >= 2  # We created at least 2 files
    
    for file_info in files:
        assert "path" in file_info
        assert "full_path" in file_info
        assert "size_bytes" in file_info
        assert file_info["size_bytes"] > 0

def test_scan_nonexistent_directory():
    """Test that FileNotFoundError is raised for missing directory."""
    with pytest.raises(FileNotFoundError):
        scan_raw_data_directory("nonexistent_dir")

def test_generate_state_checksums(temp_dir):
    """Test generating state checksums for a directory."""
    files = scan_raw_data_directory(temp_dir)
    state_data = generate_state_checksums(files)
    
    assert "generated_at" in state_data
    assert "raw_data_directory" in state_data
    assert "algorithm" in state_data
    assert "total_files" in state_data
    assert "files" in state_data
    
    assert state_data["algorithm"] == ALGORITHM
    assert state_data["total_files"] == len(files)
    
    for file_entry in state_data["files"]:
        assert "path" in file_entry
        assert "checksum" in file_entry
        assert "size_bytes" in file_entry

def test_write_state_file(temp_dir):
    """Test writing state data to a YAML file."""
    state_data = {
        "generated_at": "2023-01-01T00:00:00",
        "raw_data_directory": temp_dir,
        "algorithm": "sha256",
        "total_files": 1,
        "files": [
            {
                "path": "test.txt",
                "checksum": "abc123",
                "size_bytes": 100
            }
        ]
    }
    
    output_path = os.path.join(temp_dir, "test_state.yaml")
    written_path = write_state_file(state_data, output_path)
    
    assert written_path == output_path
    assert os.path.exists(output_path)
    
    with open(output_path, 'r') as f:
        loaded_data = yaml.safe_load(f)
    
    assert loaded_data["total_files"] == 1
    assert loaded_data["files"][0]["path"] == "test.txt"

def test_verify_state_checksums_positive(temp_dir):
    """Test verification with matching checksums."""
    # Create a file
    test_file = os.path.join(temp_dir, "verify_test.txt")
    with open(test_file, 'w') as f:
        f.write("verification content")
    
    # Generate state
    files = scan_raw_data_directory(temp_dir)
    state_data = generate_state_checksums(files)
    
    # Write state file
    state_path = os.path.join(temp_dir, "verify_state.yaml")
    write_state_file(state_data, state_path)
    
    # Verify
    result = verify_state_checksums(state_path)
    assert result is True

def test_verify_state_checksums_modified_file(temp_dir):
    """Test verification fails when file content changes."""
    # Create a file
    test_file = os.path.join(temp_dir, "modify_test.txt")
    with open(test_file, 'w') as f:
        f.write("original content")
    
    # Generate state
    files = scan_raw_data_directory(temp_dir)
    state_data = generate_state_checksums(files)
    
    # Write state file
    state_path = os.path.join(temp_dir, "modify_state.yaml")
    write_state_file(state_data, state_path)
    
    # Modify file
    with open(test_file, 'w') as f:
        f.write("modified content")
    
    # Verify should fail
    result = verify_state_checksums(state_path)
    assert result is False

def test_verify_state_checksums_missing_file(temp_dir):
    """Test verification fails when file is missing."""
    # Create a file
    test_file = os.path.join(temp_dir, "delete_test.txt")
    with open(test_file, 'w') as f:
        f.write("to be deleted")
    
    # Generate state
    files = scan_raw_data_directory(temp_dir)
    state_data = generate_state_checksums(files)
    
    # Write state file
    state_path = os.path.join(temp_dir, "delete_state.yaml")
    write_state_file(state_data, state_path)
    
    # Delete file
    os.remove(test_file)
    
    # Verify should fail
    result = verify_state_checksums(state_path)
    assert result is False
