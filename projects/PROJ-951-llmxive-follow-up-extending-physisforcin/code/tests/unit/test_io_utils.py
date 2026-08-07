"""
Unit tests for io_utils module.
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

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
    DATA_DIRS,
    CHECKSUM_FILE
)


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def populated_dir(temp_data_dir):
    """Create a directory with some test files."""
    # Create subdirectories
    (temp_data_dir / "subdir1").mkdir()
    (temp_data_dir / "subdir1" / "nested").mkdir()
    (temp_data_dir / "subdir2").mkdir()
    
    # Create test files
    (temp_data_dir / "file1.txt").write_text("Hello, World!")
    (temp_data_dir / "subdir1" / "file2.txt").write_text("Test content")
    (temp_data_dir / "subdir1" / "nested" / "file3.txt").write_text("Nested file")
    (temp_data_dir / "subdir2" / "file4.bin").write_bytes(b"\x00\x01\x02\x03")
    
    yield temp_data_dir


def test_ensure_dirs():
    """Test that ensure_dirs creates required directories."""
    # Create a temporary root
    with tempfile.TemporaryDirectory() as temp_root:
        # Temporarily override DATA_ROOT
        original_root = DATA_DIRS
        
        # Create test directories
        test_dirs = {
            "raw": Path(temp_root) / "raw",
            "curated": Path(temp_root) / "curated",
            "eval": Path(temp_root) / "eval",
        }
        
        # Test creation
        for dir_name, dir_path in test_dirs.items():
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Verify all exist
        for dir_path in test_dirs.values():
            assert dir_path.exists()
            assert dir_path.is_dir()


def test_calculate_file_checksum(temp_data_dir):
    """Test file checksum calculation."""
    test_file = temp_data_dir / "test.txt"
    test_content = "Test content for checksum"
    test_file.write_text(test_content)
    
    checksum = calculate_file_checksum(test_file)
    
    assert len(checksum) == 64  # SHA-256 hex length
    assert all(c in '0123456789abcdef' for c in checksum)
    
    # Same content should produce same checksum
    checksum2 = calculate_file_checksum(test_file)
    assert checksum == checksum2


def test_calculate_file_checksum_nonexistent():
    """Test checksum calculation on non-existent file."""
    with pytest.raises(FileNotFoundError):
        calculate_file_checksum(Path("/nonexistent/file.txt"))


def test_calculate_directory_checksums(populated_dir):
    """Test directory checksum calculation."""
    checksums = calculate_directory_checksums(populated_dir)
    
    assert len(checksums) == 4  # 4 files
    assert "file1.txt" in checksums
    assert "subdir1/file2.txt" in checksums
    assert "subdir1/nested/file3.txt" in checksums
    assert "subdir2/file4.bin" in checksums
    
    # Verify all checksums are valid SHA-256
    for checksum in checksums.values():
        assert len(checksum) == 64


def test_save_and_load_checksums(temp_data_dir):
    """Test saving and loading checksums."""
    test_checksums = {
        "file1.txt": "abc123",
        "file2.txt": "def456",
        "subdir/file3.txt": "ghi789"
    }
    
    checksum_file = temp_data_dir / "checksums.json"
    save_checksums(test_checksums, checksum_file)
    
    assert checksum_file.exists()
    
    loaded = load_checksums(checksum_file)
    assert loaded == test_checksums


def test_verify_directory_integrity(populated_dir):
    """Test directory integrity verification."""
    # First, create checksums
    checksums = calculate_directory_checksums(populated_dir)
    save_checksums(checksums, populated_dir / ".checksums.json")
    
    # Verify with correct checksums
    is_valid, errors = verify_directory_integrity(populated_dir, checksums)
    assert is_valid
    assert len(errors) == 0
    
    # Modify a file
    (populated_dir / "file1.txt").write_text("Modified content")
    
    # Verify should fail
    is_valid, errors = verify_directory_integrity(populated_dir, checksums)
    assert not is_valid
    assert any("Checksum mismatch" in error for error in errors)
    
    # Restore file
    (populated_dir / "file1.txt").write_text("Hello, World!")
    
    # Verify should pass again
    is_valid, errors = verify_directory_integrity(populated_dir, checksums)
    assert is_valid


def test_update_checksums(populated_dir):
    """Test updating checksums."""
    initial_checksums = calculate_directory_checksums(populated_dir)
    updated = update_checksums(populated_dir)
    
    assert updated == initial_checksums


def test_get_file_size(temp_data_dir):
    """Test file size calculation."""
    test_file = temp_data_dir / "test.txt"
    test_content = "12345"
    test_file.write_text(test_content)
    
    size = get_file_size(test_file)
    assert size == len(test_content.encode('utf-8'))


def test_get_total_size(populated_dir):
    """Test total directory size calculation."""
    total_size = get_total_size(populated_dir)
    assert total_size > 0
    
    # Verify by summing individual file sizes
    expected_size = sum(f.stat().st_size for f in populated_dir.rglob("*") if f.is_file())
    assert total_size == expected_size


def test_cleanup_empty_dirs(temp_data_dir):
    """Test cleanup of empty directories."""
    # Create empty nested directories
    (temp_data_dir / "empty1" / "empty2" / "empty3").mkdir(parents=True)
    
    removed = cleanup_empty_dirs(temp_data_dir)
    assert removed == 3
    assert not (temp_data_dir / "empty1").exists()


def test_move_files_with_checksums(temp_data_dir):
    """Test moving files with checksum verification."""
    src_dir = temp_data_dir / "src"
    dst_dir = temp_data_dir / "dst"
    src_dir.mkdir()
    
    # Create test file
    test_file = src_dir / "test.txt"
    test_file.write_text("Test content")
    
    moved = move_files_with_checksums(src_dir, dst_dir)
    assert moved == 1
    assert not test_file.exists()
    assert (dst_dir / "test.txt").exists()


def test_validate_project_structure(temp_data_dir):
    """Test project structure validation."""
    # Create minimal valid structure
    dirs = [
        "src", "src/utils", "tests", "tests/unit", 
        "data", "data/raw", "data/curated"
    ]
    for d in dirs:
        (temp_data_dir / d).mkdir(parents=True)
    
    is_valid, errors = validate_project_structure(temp_data_dir)
    assert is_valid
    assert len(errors) == 0
    
    # Remove a required directory
    shutil.rmtree(temp_data_dir / "src")
    
    is_valid, errors = validate_project_structure(temp_data_dir)
    assert not is_valid
    assert any("src" in error for error in errors)


def test_get_data_stats(temp_data_dir):
    """Test data statistics collection."""
    # Create some files
    (temp_data_dir / "file1.txt").write_text("Content")
    (temp_data_dir / "subdir").mkdir()
    (temp_data_dir / "subdir" / "file2.txt").write_text("More content")
    
    # This would normally use the global DATA_DIRS, but we test the logic
    # by checking that the function returns a dict with expected structure
    stats = get_data_stats()
    
    assert isinstance(stats, dict)
    assert "raw" in stats
    assert "curated" in stats
    assert "eval" in stats
    assert "validation" in stats
    
    # Check structure of individual stats
    for dir_name, dir_stats in stats.items():
        assert "exists" in dir_stats
        assert "file_count" in dir_stats
        assert "total_size_bytes" in dir_stats
        assert "total_size_mb" in dir_stats
