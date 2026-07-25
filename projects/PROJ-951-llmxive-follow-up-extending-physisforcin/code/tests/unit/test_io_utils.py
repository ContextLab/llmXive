"""
Unit tests for io_utils module.
"""
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
    """Create a temporary directory for testing."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)


def test_ensure_dirs(temp_data_dir):
    """Test that ensure_dirs creates the required directories."""
    base_path = Path(temp_data_dir)
    created = ensure_dirs(base_path)
    
    for dir_name in DATA_DIRS:
        expected_path = base_path / dir_name
        assert expected_path.exists()
        assert expected_path.is_dir()
    
    assert len(created) == len(DATA_DIRS)


def test_calculate_file_checksum(temp_data_dir):
    """Test file checksum calculation."""
    test_file = Path(temp_data_dir) / "test.txt"
    test_content = b"Hello, World!"
    test_file.write_bytes(test_content)
    
    checksum = calculate_file_checksum(test_file)
    assert isinstance(checksum, str)
    assert len(checksum) == 64  # SHA256 hex length
    
    # Verify consistency
    checksum2 = calculate_file_checksum(test_file)
    assert checksum == checksum2


def test_calculate_file_checksum_nonexistent():
    """Test that calculating checksum of non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        calculate_file_checksum("/nonexistent/path/file.txt")


def test_calculate_directory_checksums(temp_data_dir):
    """Test directory checksum calculation."""
    # Create some files
    (Path(temp_data_dir) / "file1.txt").write_bytes(b"content1")
    (Path(temp_data_dir) / "file2.txt").write_bytes(b"content2")
    (Path(temp_data_dir) / "subdir").mkdir()
    (Path(temp_data_dir) / "subdir" / "file3.txt").write_bytes(b"content3")
    
    checksums = calculate_directory_checksums(temp_data_dir)
    
    assert len(checksums) == 3
    assert "file1.txt" in checksums
    assert "file2.txt" in checksums
    assert "subdir/file3.txt" in checksums


def test_save_and_load_checksums(temp_data_dir):
    """Test saving and loading checksums."""
    test_file = Path(temp_data_dir) / "test.txt"
    test_file.write_bytes(b"test content")
    
    checksums = {
        "test.txt": calculate_file_checksum(test_file)
    }
    
    output_path = Path(temp_data_dir) / "checksums.json"
    save_checksums(checksums, output_path)
    
    assert output_path.exists()
    
    loaded = load_checksums(output_path)
    assert loaded == checksums


def test_verify_directory_integrity(temp_data_dir):
    """Test directory integrity verification."""
    # Create files and checksums
    (Path(temp_data_dir) / "file1.txt").write_bytes(b"content1")
    (Path(temp_data_dir) / "file2.txt").write_bytes(b"content2")
    
    checksums = calculate_directory_checksums(temp_data_dir)
    checksum_path = Path(temp_data_dir) / "checksums.json"
    save_checksums(checksums, checksum_path)
    
    # Verify integrity
    results = verify_directory_integrity(temp_data_dir, checksum_path)
    
    assert all(results.values())
    assert len(results) == 2
    
    # Modify a file
    (Path(temp_data_dir) / "file1.txt").write_bytes(b"modified content")
    
    results_modified = verify_directory_integrity(temp_data_dir, checksum_path)
    assert results_modified["file1.txt"] == False
    assert results_modified["file2.txt"] == True


def test_update_checksums(temp_data_dir):
    """Test updating checksums."""
    (Path(temp_data_dir) / "file1.txt").write_bytes(b"content1")
    
    checksum_path = Path(temp_data_dir) / "checksums.json"
    update_checksums(temp_data_dir, checksum_path)
    
    assert checksum_path.exists()
    loaded = load_checksums(checksum_path)
    assert "file1.txt" in loaded


def test_get_file_size(temp_data_dir):
    """Test file size retrieval."""
    test_file = Path(temp_data_dir) / "test.txt"
    test_content = b"12345"
    test_file.write_bytes(test_content)
    
    size = get_file_size(test_file)
    assert size == 5


def test_get_total_size(temp_data_dir):
    """Test total directory size."""
    (Path(temp_data_dir) / "file1.txt").write_bytes(b"12345")
    (Path(temp_data_dir) / "file2.txt").write_bytes(b"1234567890")
    
    total = get_total_size(temp_data_dir)
    assert total == 15


def test_cleanup_empty_dirs(temp_data_dir):
    """Test cleanup of empty directories."""
    # Create nested empty directories
    (Path(temp_data_dir) / "empty1").mkdir()
    (Path(temp_data_dir) / "empty1" / "empty2").mkdir()
    (Path(temp_data_dir) / "empty1" / "empty2" / "empty3").mkdir()
    
    # Create a directory with a file
    (Path(temp_data_dir) / "nonempty").mkdir()
    (Path(temp_data_dir) / "nonempty" / "file.txt").write_bytes(b"data")
    
    removed = cleanup_empty_dirs(temp_data_dir)
    
    assert removed == 3
    assert not (Path(temp_data_dir) / "empty1").exists()
    assert (Path(temp_data_dir) / "nonempty").exists()


def test_move_files_with_checksums(temp_data_dir):
    """Test moving files with checksum verification."""
    # Setup source and dest
    source = Path(temp_data_dir) / "source"
    dest = Path(temp_data_dir) / "dest"
    source.mkdir()
    
    test_file = source / "test.txt"
    test_file.write_bytes(b"test content")
    
    files = ["test.txt"]
    results = move_files_with_checksums(source, dest, files)
    
    assert results["test.txt"] == True
    assert not test_file.exists()
    assert (dest / "test.txt").exists()


def test_validate_project_structure(temp_data_dir):
    """Test project structure validation."""
    base = Path(temp_data_dir)
    
    # Initially all missing
    results = validate_project_structure(base)
    assert all(not v for v in results.values())
    
    # Create directories
    ensure_dirs(base)
    
    results = validate_project_structure(base)
    assert all(results.values())


def test_get_data_stats(temp_data_dir):
    """Test getting data statistics."""
    base = Path(temp_data_dir)
    
    # Create some files
    raw_dir = base / "data" / "raw"
    raw_dir.mkdir(parents=True)
    (raw_dir / "file1.txt").write_bytes(b"12345")
    
    stats = get_data_stats(base)
    
    assert "data/raw" in stats
    assert stats["data/raw"]["exists"] == True
    assert stats["data/raw"]["file_count"] == 1
    assert stats["data/raw"]["total_bytes"] == 5
    assert "data/curated" in stats
    assert stats["data/curated"]["exists"] == False