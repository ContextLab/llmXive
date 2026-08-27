"""
Integration tests for src.utils.io_utils
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest

import sys
code_root = Path(__file__).parent.parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.utils.io_utils import (
    calculate_directory_checksums,
    save_checksums,
    load_checksums,
    verify_directory_integrity,
    move_files_with_checksums,
    get_data_stats,
    cleanup_empty_dirs
)


@pytest.fixture
def integration_test_dir(tmp_path):
    """Setup a temporary directory for integration tests."""
    test_root = tmp_path / "integration_test"
    test_root.mkdir()
    return test_root


def test_full_workflow(integration_test_dir):
    """Test the full workflow: create -> checksum -> move -> verify."""
    src = integration_test_dir / "source"
    dst = integration_test_dir / "destination"
    checksums_file = integration_test_dir / "checksums.json"

    # 1. Create source structure
    src.mkdir()
    (src / "data.txt").write_text("important data")
    (src / "config.json").write_text('{"key": "value"}')

    # 2. Calculate and save checksums
    initial_checksums = calculate_directory_checksums(src)
    save_checksums(initial_checksums, checksums_file)

    # 3. Verify source integrity
    valid, mismatches = verify_directory_integrity(src, initial_checksums)
    assert valid, f"Source integrity failed: {mismatches}"

    # 4. Move files
    files_to_move = list(initial_checksums.keys())
    success = move_files_with_checksums(src, dst, files_to_move)
    assert success, "Move operation failed"

    # 5. Verify destination integrity
    final_checksums = load_checksums(checksums_file)
    valid, mismatches = verify_directory_integrity(dst, final_checksums)
    assert valid, f"Destination integrity failed: {mismatches}"

    # 6. Verify source is empty/missing moved files
    assert not (src / "data.txt").exists()
    assert not (src / "config.json").exists()


def test_move_and_verify(integration_test_dir):
    """Test moving a subset of files and verifying."""
    src = integration_test_dir / "src"
    dst = integration_test_dir / "dst"
    src.mkdir()

    (src / "keep.txt").write_text("keep")
    (src / "move.txt").write_text("move")

    checksums = calculate_directory_checksums(src)
    save_checksums(checksums, integration_test_dir / "all.json")

    # Move only one file
    success = move_files_with_checksums(src, dst, ["move.txt"])
    assert success

    # Verify only moved file is in dst
    assert (dst / "move.txt").exists()
    assert not (dst / "keep.txt").exists()

    # Verify source still has the other
    assert (src / "keep.txt").exists()


def test_directory_cleanup(integration_test_dir):
    """Test that directory cleanup works after moves."""
    src = integration_test_dir / "src"
    src.mkdir()
    (src / "sub").mkdir()
    (src / "sub" / "deep").mkdir()

    # Create a file to move
    (src / "sub" / "file.txt").write_text("data")

    checksums = calculate_directory_checksums(src)
    save_checksums(checksums, integration_test_dir / "cs.json")

    # Move the file
    move_files_with_checksums(src, integration_test_dir / "dst", ["sub/file.txt"])

    # Cleanup empty dirs
    removed = cleanup_empty_dirs(src)
    assert removed >= 2  # sub and deep should be removed

    assert not (src / "sub").exists()


def test_stats_across_operations(integration_test_dir):
    """Verify data stats change correctly across operations."""
    from src.utils.io_utils import get_data_stats

    src = integration_test_dir / "src"
    src.mkdir()
    (src / "file.txt").write_text("x" * 100)

    stats_before = get_data_stats(src)
    assert stats_before["file_count"] == 1
    assert stats_before["total_size_bytes"] == 100

    # Move file
    dst = integration_test_dir / "dst"
    move_files_with_checksums(src, dst, ["file.txt"])

    stats_after_src = get_data_stats(src)
    stats_after_dst = get_data_stats(dst)

    assert stats_after_src["file_count"] == 0
    assert stats_after_dst["file_count"] == 1
    assert stats_after_dst["total_size_bytes"] == 100