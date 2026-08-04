import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest

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
    get_data_stats,
    DATA_DIRS
)

@pytest.fixture
def temp_data_dir():
    """Creates a temporary directory for testing."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir, ignore_errors=True)

@pytest.fixture
def populated_dir(temp_data_dir):
    """Creates a temporary directory with some files."""
    (temp_data_dir / "subdir").mkdir()
    (temp_data_dir / "file1.txt").write_text("content1")
    (temp_data_dir / "subdir" / "file2.txt").write_text("content2")
    return temp_data_dir

def test_ensure_dirs(temp_data_dir):
    """Test that ensure_dirs creates the required structure."""
    # Simulate base path
    created = ensure_dirs(temp_data_dir)
    
    for dir_path in DATA_DIRS:
        expected = temp_data_dir / dir_path
        assert expected.exists(), f"Directory {expected} was not created"
        assert expected.is_dir(), f"{expected} is not a directory"

def test_calculate_file_checksum(temp_data_dir):
    """Test file checksum calculation."""
    test_file = temp_data_dir / "test.txt"
    test_file.write_text("Hello World")
    
    checksum = calculate_file_checksum(test_file)
    assert len(checksum) == 64  # SHA256 hex length
    assert isinstance(checksum, str)
    
    # Verify consistency
    checksum2 = calculate_file_checksum(test_file)
    assert checksum == checksum2

def test_calculate_file_checksum_nonexistent(temp_data_dir):
    """Test checksum calculation on nonexistent file."""
    with pytest.raises(FileNotFoundError):
        calculate_file_checksum(temp_data_dir / "nonexistent.txt")

def test_calculate_directory_checksums(populated_dir):
    """Test directory checksum calculation."""
    checksums = calculate_directory_checksums(populated_dir)
    
    assert "file1.txt" in checksums
    assert "subdir/file2.txt" in checksums
    assert len(checksums) == 2

def test_save_and_load_checksums(temp_data_dir):
    """Test saving and loading checksums."""
    test_data = {"file1.txt": "abc123", "file2.txt": "def456"}
    output_path = temp_data_dir / "checksums.json"
    
    save_checksums(test_data, output_path)
    assert output_path.exists()
    
    loaded = load_checksums(output_path)
    assert loaded == test_data

def test_verify_directory_integrity(temp_data_dir):
    """Test directory integrity verification."""
    # Create files
    (temp_data_dir / "a.txt").write_text("1")
    (temp_data_dir / "b.txt").write_text("2")
    
    # Calculate expected
    expected = calculate_directory_checksums(temp_data_dir)
    
    # Verify valid
    is_valid, mismatches = verify_directory_integrity(temp_data_dir, expected)
    assert is_valid
    assert len(mismatches) == 0
    
    # Corrupt a file
    (temp_data_dir / "a.txt").write_text("CORRUPTED")
    is_valid, mismatches = verify_directory_integrity(temp_data_dir, expected)
    assert not is_valid
    assert len(mismatches) == 1

def test_update_checksums(populated_dir):
    """Test updating checksums."""
    checksum_file = populated_dir.parent / "checksums.json"
    update_checksums(populated_dir, checksum_file)
    
    assert checksum_file.exists()
    loaded = load_checksums(checksum_file)
    assert len(loaded) > 0

def test_get_file_size(temp_data_dir):
    """Test file size retrieval."""
    test_file = temp_data_dir / "size_test.txt"
    content = "0123456789"
    test_file.write_text(content)
    
    size = get_file_size(test_file)
    assert size == len(content)

def test_get_total_size(populated_dir):
    """Test total directory size."""
    total = get_total_size(populated_dir)
    assert total > 0

def test_cleanup_empty_dirs(temp_data_dir):
    """Test cleanup of empty directories."""
    # Create nested empty dirs
    nested = temp_data_dir / "empty" / "nested"
    nested.mkdir(parents=True)
    
    removed = cleanup_empty_dirs(temp_data_dir)
    assert removed == 2
    assert not nested.exists()

def test_move_files_with_checksums(temp_data_dir):
    """Test moving files with checksum verification."""
    src = temp_data_dir / "src"
    dst = temp_data_dir / "dst"
    src.mkdir()
    dst.mkdir()
    
    test_file = src / "move_me.txt"
    test_file.write_text("move content")
    
    moved = move_files_with_checksums(src, dst, ["move_me.txt"])
    
    assert len(moved) == 1
    assert (dst / "move_me.txt").exists()
    assert not test_file.exists()

def test_validate_project_structure(temp_data_dir):
    """Test project structure validation."""
    # Initially missing
    is_valid, missing = validate_project_structure(temp_data_dir)
    assert not is_valid
    assert len(missing) > 0
    
    # Create structure
    ensure_dirs(temp_data_dir)
    is_valid, missing = validate_project_structure(temp_data_dir)
    assert is_valid
    assert len(missing) == 0

def test_get_data_stats(temp_data_dir):
    """Test getting data statistics."""
    stats = get_data_stats(temp_data_dir)
    assert stats["file_count"] == 0
    assert stats["total_size"] == 0
    
    # Add files
    (temp_data_dir / "f1.txt").write_text("123")
    (temp_data_dir / "f2.txt").write_text("4567")
    
    stats = get_data_stats(temp_data_dir)
    assert stats["file_count"] == 2
    assert stats["total_size"] == 7
    assert stats["avg_size"] == 3.5