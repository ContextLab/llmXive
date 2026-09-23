"""
Unit tests for checksum_utils module.
"""
import os
import tempfile
import hashlib
from pathlib import Path
import pytest

import sys
# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from checksum_utils import compute_checksum, generate_checksums, verify_checksums, update_checksum_for_file

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_compute_checksum(temp_dir):
    """Test that compute_checksum returns correct SHA256 hash."""
    # Create a test file
    test_file = temp_dir / "test.txt"
    content = b"Hello, World!"
    test_file.write_bytes(content)

    expected_hash = hashlib.sha256(content).hexdigest()
    actual_hash = compute_checksum(test_file)

    assert actual_hash == expected_hash

def test_compute_checksum_nonexistent_file(temp_dir):
    """Test that compute_checksum raises FileNotFoundError for missing file."""
    nonexistent = temp_dir / "does_not_exist.txt"
    with pytest.raises(FileNotFoundError):
        compute_checksum(nonexistent)

def test_generate_checksums(temp_dir):
    """Test that generate_checksums creates correct output file."""
    # Create some test files
    (temp_dir / "file1.txt").write_text("content1")
    (temp_dir / "subdir").mkdir()
    (temp_dir / "subdir" / "file2.txt").write_text("content2")

    output_file = temp_dir / "checksums.txt"
    
    generate_checksums(temp_dir, output_file)

    assert output_file.exists()
    content = output_file.read_text()
    
    # Verify format: "hash  relative_path"
    lines = content.strip().split('\n')
    assert len(lines) == 2
    
    for line in lines:
        parts = line.split('  ', 1)
        assert len(parts) == 2
        assert len(parts[0]) == 64  # SHA256 hex length

def test_verify_checksums_success(temp_dir):
    """Test successful verification of checksums."""
    # Create files and generate checksums
    (temp_dir / "file1.txt").write_text("content1")
    output_file = temp_dir / "checksums.txt"
    generate_checksums(temp_dir, output_file)

    # Verify
    all_valid, failed = verify_checksums(output_file, temp_dir)
    
    assert all_valid is True
    assert len(failed) == 0

def test_verify_checksums_failure(temp_dir):
    """Test verification fails when file content changes."""
    # Create file and generate checksums
    test_file = temp_dir / "file1.txt"
    test_file.write_text("original")
    output_file = temp_dir / "checksums.txt"
    generate_checksums(temp_dir, output_file)

    # Modify file
    test_file.write_text("modified")

    # Verify should fail
    all_valid, failed = verify_checksums(output_file, temp_dir)
    
    assert all_valid is False
    assert len(failed) == 1
    assert "file1.txt" in failed[0]

def test_verify_checksums_missing_file(temp_dir):
    """Test verification fails when file is deleted."""
    # Create file and generate checksums
    test_file = temp_dir / "file1.txt"
    test_file.write_text("content")
    output_file = temp_dir / "checksums.txt"
    generate_checksums(temp_dir, output_file)

    # Delete file
    test_file.unlink()

    # Verify should fail
    all_valid, failed = verify_checksums(output_file, temp_dir)
    
    assert all_valid is False
    assert len(failed) == 1

def test_update_checksum_for_file(temp_dir):
    """Test updating a single file's checksum."""
    test_file = temp_dir / "file1.txt"
    test_file.write_text("original")
    output_file = temp_dir / "checksums.txt"
    
    # Generate initial checksums
    generate_checksums(temp_dir, output_file)
    
    # Modify file
    test_file.write_text("modified")
    
    # Update checksum
    update_checksum_for_file(test_file, output_file)
    
    # Verify updated checksum
    all_valid, failed = verify_checksums(output_file, temp_dir)
    assert all_valid is True