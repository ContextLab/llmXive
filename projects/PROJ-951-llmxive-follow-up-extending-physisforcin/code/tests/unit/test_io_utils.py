"""
Unit tests for I/O utilities in src/utils/io_utils.py
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import logging

from src.utils.io_utils import (
    ensure_dirs,
    calculate_file_checksum,
    calculate_directory_checksums,
    save_checksums,
    load_checksums,
    verify_directory_integrity,
    update_checksums,
    get_file_size,
    get_total_size,
    cleanup_empty_dirs,
    move_files_with_checksums,
    validate_project_structure,
    get_data_stats
)

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_ensure_dirs(temp_data_dir):
    """Test that ensure_dirs creates the required directory structure."""
    base = ensure_dirs(temp_data_dir)
    
    # Check that base is the temp directory
    assert base == temp_data_dir
    
    # Check that data subdirectories were created
    for subdir in ['raw', 'curated', 'eval']:
        dir_path = base / 'data' / subdir
        assert dir_path.exists(), f"Directory {dir_path} was not created"
        assert dir_path.is_dir(), f"{dir_path} is not a directory"


def test_calculate_file_checksum(temp_data_dir):
    """Test file checksum calculation."""
    # Create a test file
    test_file = temp_data_dir / 'test.txt'
    content = b"Hello, World!"
    test_file.write_bytes(content)
    
    # Calculate checksum
    checksum = calculate_file_checksum(test_file)
    
    # Verify it's a valid hex string
    assert len(checksum) == 64  # SHA256 produces 64 hex characters
    assert all(c in '0123456789abcdef' for c in checksum)
    
    # Verify consistency
    checksum2 = calculate_file_checksum(test_file)
    assert checksum == checksum2
    
    # Verify known value for known content
    expected = 'dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f'
    assert checksum == expected, f"Expected {expected}, got {checksum}"


def test_calculate_file_checksum_nonexistent():
    """Test that calculating checksum of non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        calculate_file_checksum('/nonexistent/file.txt')


def test_calculate_directory_checksums(temp_data_dir):
    """Test directory checksum calculation."""
    # Create test files
    (temp_data_dir / 'file1.txt').write_text('content1')
    (temp_data_dir / 'file2.txt').write_text('content2')
    subdir = temp_data_dir / 'subdir'
    subdir.mkdir()
    (subdir / 'file3.txt').write_text('content3')
    
    checksums = calculate_directory_checksums(temp_data_dir)
    
    # Check that all files are included
    assert 'file1.txt' in checksums
    assert 'file2.txt' in checksums
    assert 'subdir/file3.txt' in checksums
    
    # Check that checksums are valid
    for checksum in checksums.values():
        assert len(checksum) == 64
        assert all(c in '0123456789abcdef' for c in checksum)


def test_save_and_load_checksums(temp_data_dir):
    """Test saving and loading checksums."""
    checksums = {
        'file1.txt': 'abc123',
        'file2.txt': 'def456',
        'subdir/file3.txt': 'ghi789'
    }
    
    checksum_file = temp_data_dir / 'checksums.json'
    
    # Save checksums
    save_checksums(checksums, checksum_file)
    
    # Verify file was created
    assert checksum_file.exists()
    
    # Load checksums
    loaded = load_checksums(checksum_file)
    
    # Verify loaded checksums match
    assert loaded == checksums


def test_verify_directory_integrity(temp_data_dir):
    """Test directory integrity verification."""
    # Create test files
    (temp_data_dir / 'file1.txt').write_text('content1')
    (temp_data_dir / 'file2.txt').write_text('content2')
    
    # Calculate actual checksums
    actual_checksums = calculate_directory_checksums(temp_data_dir)
    
    # Verify with correct checksums
    is_valid, failed = verify_directory_integrity(temp_data_dir, actual_checksums)
    assert is_valid
    assert len(failed) == 0
    
    # Verify with incorrect checksums
    wrong_checksums = actual_checksums.copy()
    wrong_checksums['file1.txt'] = 'wrong_checksum'
    is_valid, failed = verify_directory_integrity(temp_data_dir, wrong_checksums)
    assert not is_valid
    assert len(failed) == 1
    assert 'file1.txt' in failed[0]
    
    # Verify with missing file
    missing_checksums = actual_checksums.copy()
    del missing_checksums['file1.txt']
    missing_checksums['nonexistent.txt'] = 'some_checksum'
    is_valid, failed = verify_directory_integrity(temp_data_dir, missing_checksums)
    assert not is_valid
    assert len(failed) == 1
    assert 'nonexistent.txt' in failed[0]


def test_update_checksums(temp_data_dir):
    """Test updating checksums."""
    # Create test files
    (temp_data_dir / 'file1.txt').write_text('content1')
    
    checksum_file = temp_data_dir / 'checksums.json'
    
    # Update checksums
    new_checksums = update_checksums(temp_data_dir, checksum_file)
    
    # Verify checksums were saved
    assert checksum_file.exists()
    loaded = load_checksums(checksum_file)
    assert loaded == new_checksums
    
    # Verify checksum is correct
    assert 'file1.txt' in new_checksums
    assert len(new_checksums['file1.txt']) == 64


def test_get_file_size(temp_data_dir):
    """Test file size calculation."""
    test_file = temp_data_dir / 'test.txt'
    content = b"Hello"  # 5 bytes
    test_file.write_bytes(content)
    
    size = get_file_size(test_file)
    assert size == 5


def test_get_total_size(temp_data_dir):
    """Test total directory size calculation."""
    # Create files with known sizes
    (temp_data_dir / 'file1.txt').write_bytes(b"12345")  # 5 bytes
    (temp_data_dir / 'file2.txt').write_bytes(b"1234567890")  # 10 bytes
    
    total = get_total_size(temp_data_dir)
    assert total == 15


def test_cleanup_empty_dirs(temp_data_dir):
    """Test cleanup of empty directories."""
    # Create structure with empty dirs
    (temp_data_dir / 'non_empty').mkdir()
    (temp_data_dir / 'non_empty' / 'file.txt').write_text('content')
    
    (temp_data_dir / 'empty1').mkdir()
    (temp_data_dir / 'empty2').mkdir()
    (temp_data_dir / 'empty2' / 'empty3').mkdir()
    
    # Cleanup
    removed = cleanup_empty_dirs(temp_data_dir)
    
    # Verify empty dirs were removed
    assert not (temp_data_dir / 'empty1').exists()
    assert not (temp_data_dir / 'empty2').exists()
    assert not (temp_data_dir / 'empty2' / 'empty3').exists()
    
    # Verify non-empty dir remains
    assert (temp_data_dir / 'non_empty').exists()
    assert (temp_data_dir / 'non_empty' / 'file.txt').exists()
    
    # Verify count
    assert removed == 3  # empty1, empty2, empty3


def test_move_files_with_checksums(temp_data_dir):
    """Test moving files with checksums."""
    # Create source structure
    src = temp_data_dir / 'src'
    src.mkdir()
    (src / 'file1.txt').write_text('content1')
    (src / 'file2.txt').write_text('content2')
    
    dst = temp_data_dir / 'dst'
    checksum_file = temp_data_dir / 'checksums.json'
    
    # Move files
    files_to_move = ['file1.txt', 'file2.txt']
    checksums = move_files_with_checksums(src, dst, files_to_move, checksum_file)
    
    # Verify files were moved
    assert not (src / 'file1.txt').exists()
    assert not (src / 'file2.txt').exists()
    assert (dst / 'file1.txt').exists()
    assert (dst / 'file2.txt').exists()
    
    # Verify checksums were calculated
    assert len(checksums) == 2
    assert 'file1.txt' in checksums
    assert 'file2.txt' in checksums
    
    # Verify checksum file was created
    assert checksum_file.exists()
    loaded = load_checksums(checksum_file)
    assert loaded == checksums


def test_validate_project_structure(temp_data_dir):
    """Test project structure validation."""
    # Create minimal valid structure
    required = [
        'data/raw', 'data/curated', 'data/eval',
        'src/generation', 'src/filtering', 'src/training', 
        'src/evaluation', 'src/utils',
        'tests/unit', 'tests/integration'
    ]
    
    for dir_path in required:
        (temp_data_dir / dir_path).mkdir(parents=True)
    
    is_valid, missing = validate_project_structure(temp_data_dir)
    assert is_valid
    assert len(missing) == 0
    
    # Test with missing directories
    (temp_data_dir / 'data/raw').rmdir()
    is_valid, missing = validate_project_structure(temp_data_dir)
    assert not is_valid
    assert 'data/raw' in missing


def test_get_data_stats(temp_data_dir):
    """Test data statistics collection."""
    # Create data structure with files
    for subdir in ['raw', 'curated', 'eval']:
        dir_path = temp_data_dir / 'data' / subdir
        dir_path.mkdir(parents=True)
        (dir_path / f'{subdir}_file.txt').write_text('content')
    
    stats = get_data_stats(temp_data_dir)
    
    # Verify all directories are in stats
    for subdir in ['raw', 'curated', 'eval']:
        assert subdir in stats
        assert stats[subdir]['exists'] is True
        assert stats[subdir]['file_count'] == 1
        assert stats[subdir]['total_size_bytes'] > 0
        
    # Verify size conversions
    for subdir in ['raw', 'curated', 'eval']:
        total_bytes = stats[subdir]['total_size_bytes']
        assert stats[subdir]['total_size_mb'] == total_bytes / (1024 * 1024)
        assert stats[subdir]['total_size_gb'] == total_bytes / (1024 * 1024 * 1024)