"""
Unit tests for T012f checksum recording functionality.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# Mock the config module for testing
import sys
from unittest.mock import patch, MagicMock

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_file(temp_dir):
    """Create a sample file for checksum testing."""
    file_path = temp_dir / "test_file.txt"
    file_path.write_text("Hello, World!")
    return file_path

def test_compute_sha256(sample_file):
    """Test SHA-256 computation on a sample file."""
    # Import the function after setting up mocks
    with patch('code.config.PROJECT_ROOT', sample_file.parent.parent):
        from checksums import compute_sha256
        
        hash_result = compute_sha256(sample_file)
        
        assert hash_result is not None
        assert len(hash_result) == 64  # SHA-256 hex string length
        assert all(c in '0123456789abcdef' for c in hash_result)

def test_compute_sha256_nonexistent_file():
    """Test SHA-256 computation on a non-existent file."""
    from checksums import compute_sha256
    
    fake_path = Path("/nonexistent/file.txt")
    hash_result = compute_sha256(fake_path)
    
    assert hash_result is None

def test_load_existing_checksums(temp_dir):
    """Test loading existing checksums from file."""
    checksum_file = temp_dir / "checksums.json"
    
    # Test with non-existent file
    from code.t012f_checksum_record import load_existing_checksums
    result = load_existing_checksums(checksum_file)
    assert result == {"checksums": []}
    
    # Test with existing file
    test_data = {"checksums": [{"filename": "test.txt", "hash": "abc123"}]}
    checksum_file.write_text(json.dumps(test_data))
    result = load_existing_checksums(checksum_file)
    assert result == test_data

def test_save_checksums(temp_dir):
    """Test saving checksums to file."""
    checksum_file = temp_dir / "checksums.json"
    test_data = {"checksums": [{"filename": "test.txt", "hash": "abc123"}]}
    
    from code.t012f_checksum_record import save_checksums
    save_checksums(checksum_file, test_data)
    
    assert checksum_file.exists()
    with open(checksum_file, 'r') as f:
        loaded_data = json.load(f)
    assert loaded_data == test_data

def test_find_dataset_archive(temp_dir):
    """Test finding dataset archive in directory."""
    from code.t012f_checksum_record import find_dataset_archive
    
    # Create test archives
    (temp_dir / "dataset.zip").write_text("dummy")
    (temp_dir / "data.tar.gz").write_text("dummy")
    (temp_dir / "other.txt").write_text("dummy")
    
    archive = find_dataset_archive(temp_dir)
    assert archive is not None
    assert archive.suffix in ['.zip', '.gz']

def test_find_dataset_archive_empty(temp_dir):
    """Test finding dataset archive in empty directory."""
    from code.t012f_checksum_record import find_dataset_archive
    
    archive = find_dataset_archive(temp_dir)
    assert archive is None

def test_find_dataset_archive_no_standard(temp_dir):
    """Test finding dataset when no standard archives exist."""
    from code.t012f_checksum_record import find_dataset_archive
    
    # Create a large file (simulating dataset)
    large_file = temp_dir / "large_dataset.bin"
    large_file.write_bytes(b"0" * 10000)
    small_file = temp_dir / "small.txt"
    small_file.write_text("small")
    
    archive = find_dataset_archive(temp_dir)
    assert archive is not None
    assert archive.name == "large_dataset.bin"
