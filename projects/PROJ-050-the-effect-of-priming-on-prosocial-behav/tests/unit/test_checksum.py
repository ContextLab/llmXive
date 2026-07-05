"""
Unit tests for the checksum utility.
"""
import json
import tempfile
from pathlib import Path
import pytest
import hashlib

from code.utils.checksum import (
    compute_file_checksum,
    save_checksums,
    load_checksums,
    verify_checksum,
    verify_all_checksums,
    generate_and_save_checksums,
    CHECKSUM_FILE_NAME
)
from code.config import PROJECT_ROOT


@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file with known content."""
    file_path = tmp_path / "test_file.txt"
    content = "Hello, World! This is a test file."
    file_path.write_text(content)
    return file_path, content


@pytest.fixture
def temp_checksum_file(tmp_path):
    """Create a temporary checksum file."""
    checksum_path = tmp_path / CHECKSUM_FILE_NAME
    checksums = {
        "test_file.txt": "abc123"
    }
    with open(checksum_path, "w") as f:
        json.dump({"version": "1.0", "algorithm": "sha256", "files": checksums}, f)
    return checksum_path


def test_compute_file_checksum(temp_file):
    """Test that checksum is computed correctly."""
    file_path, content = temp_file
    expected_hash = hashlib.sha256(content.encode()).hexdigest()
    actual_hash = compute_file_checksum(file_path)
    assert actual_hash == expected_hash
    assert len(actual_hash) == 64  # SHA-256 hex length


def test_compute_file_checksum_nonexistent():
    """Test that FileNotFoundError is raised for non-existent file."""
    with pytest.raises(FileNotFoundError):
        compute_file_checksum(Path("/nonexistent/file.txt"))


def test_save_and_load_checksums(tmp_path):
    """Test saving and loading checksums."""
    checksum_path = tmp_path / CHECKSUM_FILE_NAME
    checksums = {
        "file1.txt": "hash1",
        "file2.txt": "hash2"
    }
    
    # Save
    saved_path = save_checksums(checksums, checksum_path)
    assert saved_path.exists()
    
    # Load
    loaded_checksums = load_checksums(checksum_path)
    assert loaded_checksums == checksums


def test_verify_checksum_match(tmp_path, temp_file):
    """Test successful checksum verification."""
    file_path, content = temp_file
    expected_hash = hashlib.sha256(content.encode()).hexdigest()
    
    assert verify_checksum(file_path, expected_hash)


def test_verify_checksum_mismatch(tmp_path, temp_file):
    """Test failed checksum verification."""
    file_path, _ = temp_file
    wrong_hash = "a" * 64
    
    assert not verify_checksum(file_path, wrong_hash)


def test_verify_checksum_nonexistent_file():
    """Test verification of non-existent file."""
    assert not verify_checksum(Path("/nonexistent/file.txt"), "somehash")


def test_verify_all_checksums(tmp_path, temp_file):
    """Test verification of all checksums."""
    file_path, content = temp_file
    expected_hash = hashlib.sha256(content.encode()).hexdigest()
    
    # Create checksum file
    checksum_path = tmp_path / CHECKSUM_FILE_NAME
    checksums = {
        str(file_path): expected_hash
    }
    with open(checksum_path, "w") as f:
        json.dump({"version": "1.0", "algorithm": "sha256", "files": checksums}, f)
    
    # Verify all
    results = verify_all_checksums(checksum_path)
    assert len(results) == 1
    assert results[str(file_path)] is True


def test_generate_and_save_checksums(tmp_path):
    """Test generating and saving checksums for multiple files."""
    # Create test files
    files = []
    for i in range(3):
        file_path = tmp_path / f"test_file_{i}.txt"
        content = f"Content {i}"
        file_path.write_text(content)
        files.append(file_path)
    
    # Generate checksums
    checksum_path = tmp_path / CHECKSUM_FILE_NAME
    saved_path = generate_and_save_checksums(files, checksum_path)
    
    assert saved_path.exists()
    
    # Verify checksums
    loaded_checksums = load_checksums(checksum_path)
    assert len(loaded_checksums) == 3
    
    for file_path in files:
        expected_hash = hashlib.sha256(file_path.read_text().encode()).hexdigest()
        rel_path = str(file_path)
        assert loaded_checksums[rel_path] == expected_hash