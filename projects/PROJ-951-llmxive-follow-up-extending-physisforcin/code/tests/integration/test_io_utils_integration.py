"""
Integration tests for io_utils module.
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

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
def integration_test_dir():
    """Create a temporary directory for integration testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_full_workflow(integration_test_dir):
    """Test complete workflow: create dirs, add files, checksum, verify, modify, re-verify."""
    # Setup test directories
    raw_dir = integration_test_dir / "raw"
    curated_dir = integration_test_dir / "curated"
    raw_dir.mkdir()
    curated_dir.mkdir()
    
    # Create test files
    (raw_dir / "video1.mp4").write_bytes(b"fake_video_data_1")
    (raw_dir / "video2.mp4").write_bytes(b"fake_video_data_2")
    (curated_dir / "filtered1.mp4").write_bytes(b"filtered_data_1")
    
    # Calculate and save checksums
    checksums = calculate_directory_checksums(integration_test_dir)
    save_checksums(checksums, integration_test_dir / ".checksums.json")
    
    # Verify integrity
    is_valid, errors = verify_directory_integrity(integration_test_dir, checksums)
    assert is_valid, f"Integrity check failed: {errors}"
    
    # Modify a file
    (raw_dir / "video1.mp4").write_bytes(b"modified_data")
    
    # Verify should fail
    is_valid, errors = verify_directory_integrity(integration_test_dir, checksums)
    assert not is_valid
    assert any("Checksum mismatch" in error for error in errors)
    
    # Update checksums
    updated_checksums = update_checksums(integration_test_dir)
    
    # Verify should pass now
    is_valid, errors = verify_directory_integrity(integration_test_dir, updated_checksums)
    assert is_valid


def test_move_and_verify(integration_test_dir):
    """Test moving files with checksum verification."""
    src_dir = integration_test_dir / "source"
    dst_dir = integration_test_dir / "destination"
    src_dir.mkdir()
    
    # Create files
    (src_dir / "file1.txt").write_text("Content 1")
    (src_dir / "file2.txt").write_text("Content 2")
    (src_dir / "subdir").mkdir()
    (src_dir / "subdir" / "nested.txt").write_text("Nested")
    
    # Move files
    moved = move_files_with_checksums(src_dir, dst_dir)
    assert moved == 3
    
    # Verify destination has all files
    assert (dst_dir / "file1.txt").exists()
    assert (dst_dir / "file2.txt").exists()
    assert (dst_dir / "subdir" / "nested.txt").exists()
    
    # Verify source is empty
    assert not list(src_dir.rglob("*"))


def test_directory_cleanup(integration_test_dir):
    """Test cleanup of empty directories after file operations."""
    # Create nested empty directories
    nested = integration_test_dir / "a" / "b" / "c"
    nested.mkdir(parents=True)
    
    # Add a file at top level
    (integration_test_dir / "keep.txt").write_text("Keep this")
    
    # Clean up
    removed = cleanup_empty_dirs(integration_test_dir)
    assert removed == 3  # a, b, c
    
    # Verify structure
    assert not (integration_test_dir / "a").exists()
    assert (integration_test_dir / "keep.txt").exists()


def test_stats_across_operations(integration_test_dir):
    """Test statistics tracking across directory operations."""
    # Create initial structure
    (integration_test_dir / "data" / "raw").mkdir(parents=True)
    (integration_test_dir / "data" / "curated").mkdir(parents=True)
    
    (integration_test_dir / "data" / "raw" / "file1.txt").write_text("A" * 100)
    (integration_test_dir / "data" / "curated" / "file2.txt").write_text("B" * 200)
    
    stats = get_data_stats()
    
    # Check raw stats
    assert stats["raw"]["exists"]
    assert stats["raw"]["file_count"] == 1
    assert stats["raw"]["total_size_bytes"] == 100
    
    # Check curated stats
    assert stats["curated"]["exists"]
    assert stats["curated"]["file_count"] == 1
    assert stats["curated"]["total_size_bytes"] == 200
    
    # Add more files
    (integration_test_dir / "data" / "raw" / "file3.txt").write_text("C" * 50)
    
    stats = get_data_stats()
    assert stats["raw"]["file_count"] == 2
    assert stats["raw"]["total_size_bytes"] == 150