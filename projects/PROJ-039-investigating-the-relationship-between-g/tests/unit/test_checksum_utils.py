"""
Unit tests for checksum_utils module.
"""
import os
import tempfile
import pytest
from pathlib import Path
import hashlib

from checksum_utils import (
    compute_checksum,
    generate_checksums,
    verify_checksums,
    update_checksum_for_file
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / 'data'
        data_dir.mkdir()
        
        # Create subdirectories
        (data_dir / 'subdir1').mkdir()
        (data_dir / 'subdir2').mkdir()
        
        # Create test files
        (data_dir / 'file1.txt').write_text('Hello, World!')
        (data_dir / 'subdir1' / 'file2.txt').write_text('Test content')
        (data_dir / 'subdir2' / 'file3.txt').write_text('Another file')
        
        yield str(data_dir)

@pytest.fixture
def temp_checksum_file():
    """Create a temporary checksum file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        yield f.name
    os.unlink(f.name)

def test_compute_checksum_file_exists(temp_data_dir):
    """Test checksum computation for an existing file."""
    file_path = os.path.join(temp_data_dir, 'file1.txt')
    checksum = compute_checksum(file_path)
    
    # Verify it's a valid SHA256 hash
    assert len(checksum) == 64
    assert all(c in '0123456789abcdef' for c in checksum)
    
    # Verify against expected hash
    expected = hashlib.sha256(b'Hello, World!').hexdigest()
    assert checksum == expected

def test_compute_checksum_nonexistent_file():
    """Test that computing checksum for non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        compute_checksum('/nonexistent/path/file.txt')

def test_compute_checksum_directory(temp_data_dir):
    """Test that computing checksum for a directory raises error."""
    with pytest.raises(ValueError):
        compute_checksum(temp_data_dir)

def test_generate_checksums(temp_data_dir, temp_checksum_file):
    """Test generating checksums for all files in a directory."""
    checksums = generate_checksums(temp_data_dir, temp_checksum_file)
    
    # Check that all files are included
    assert len(checksums) == 3
    assert 'file1.txt' in checksums
    assert 'subdir1/file2.txt' in checksums
    assert 'subdir2/file3.txt' in checksums
    
    # Verify checksum file was created
    assert os.path.exists(temp_checksum_file)
    
    # Verify file contents format
    with open(temp_checksum_file, 'r') as f:
        lines = f.readlines()
    assert len(lines) == 3
    for line in lines:
        parts = line.split('  ')
        assert len(parts) == 2
        assert len(parts[0]) == 64  # SHA256 hash length

def test_generate_checksums_empty_directory(temp_checksum_file):
    """Test generating checksums for an empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        empty_dir = os.path.join(tmpdir, 'empty')
        os.makedirs(empty_dir)
        
        checksums = generate_checksums(empty_dir, temp_checksum_file)
        assert checksums == {}

def test_verify_checksums_success(temp_data_dir, temp_checksum_file):
    """Test successful verification of checksums."""
    # Generate checksums first
    generate_checksums(temp_data_dir, temp_checksum_file)
    
    # Verify
    all_valid, failed = verify_checksums(temp_checksum_file, temp_data_dir)
    assert all_valid
    assert len(failed) == 0

def test_verify_checksums_modified_file(temp_data_dir, temp_checksum_file):
    """Test verification fails when file is modified."""
    # Generate checksums
    generate_checksums(temp_data_dir, temp_checksum_file)
    
    # Modify a file
    file_path = os.path.join(temp_data_dir, 'file1.txt')
    with open(file_path, 'w') as f:
        f.write('Modified content')
    
    # Verify should fail
    all_valid, failed = verify_checksums(temp_checksum_file, temp_data_dir)
    assert not all_valid
    assert 'file1.txt' in failed
    assert failed['file1.txt'] == 'mismatch'

def test_verify_checksums_missing_file(temp_data_dir, temp_checksum_file):
    """Test verification fails when file is missing."""
    # Generate checksums
    generate_checksums(temp_data_dir, temp_checksum_file)
    
    # Delete a file
    os.remove(os.path.join(temp_data_dir, 'file1.txt'))
    
    # Verify should fail
    all_valid, failed = verify_checksums(temp_checksum_file, temp_data_dir)
    assert not all_valid
    assert 'file1.txt' in failed
    assert failed['file1.txt'] == 'File not found'

def test_update_checksum_for_file(temp_data_dir, temp_checksum_file):
    """Test updating checksum for a single file."""
    # Create initial checksum file
    file_path = os.path.join(temp_data_dir, 'file1.txt')
    update_checksum_for_file(file_path, temp_checksum_file)
    
    # Verify file was created
    assert os.path.exists(temp_checksum_file)
    
    # Modify file and update again
    with open(file_path, 'w') as f:
        f.write('Updated content')
    
    update_checksum_for_file(file_path, temp_checksum_file)
    
    # Verify new checksum is in file
    with open(temp_checksum_file, 'r') as f:
        content = f.read()
    
    new_checksum = hashlib.sha256(b'Updated content').hexdigest()
    assert new_checksum in content

def test_update_checksum_for_new_file(temp_data_dir, temp_checksum_file):
    """Test updating checksum for a file not previously in the checksum file."""
    # Create a new file
    new_file = os.path.join(temp_data_dir, 'new_file.txt')
    with open(new_file, 'w') as f:
        f.write('New file content')
    
    # Update checksum
    update_checksum_for_file(new_file, temp_checksum_file)
    
    # Verify file was created
    assert os.path.exists(temp_checksum_file)
    
    # Verify checksum is in file
    with open(temp_checksum_file, 'r') as f:
        content = f.read()
    
    expected_checksum = hashlib.sha256(b'New file content').hexdigest()
    assert expected_checksum in content
    assert 'new_file.txt' in content