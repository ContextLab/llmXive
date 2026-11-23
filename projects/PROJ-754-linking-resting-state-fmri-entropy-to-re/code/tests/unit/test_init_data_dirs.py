import os
import sys
import tempfile
import hashlib
from pathlib import Path
import pytest

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from scripts.init_data_dirs import (
    get_project_root,
    ensure_directory,
    compute_sha256,
    append_checksum,
    scan_and_log_checksums
)

def test_get_project_root():
    """Test that project root is correctly identified."""
    root = get_project_root()
    assert isinstance(root, Path)
    assert root.exists()
    # Should be the root of the repository
    assert (root / "code").exists()

def test_ensure_directory():
    """Test directory creation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "new_subdir"
        ensure_directory(test_dir)
        assert test_dir.exists()
        assert test_dir.is_dir()

def test_compute_sha256():
    """Test SHA-256 computation."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test content")
        temp_path = Path(f.name)

    try:
        checksum = compute_sha256(temp_path)
        # SHA-256 of "test content"
        expected = hashlib.sha256(b"test content").hexdigest()
        assert checksum == expected
        assert len(checksum) == 64  # Hex SHA-256 length
    finally:
        temp_path.unlink()

def test_append_checksum():
    """Test checksum appending to file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        checksum_file = Path(tmpdir) / "checksums.txt"
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("data")

        checksum = compute_sha256(test_file)
        append_checksum(checksum_file, "test.txt", checksum)

        assert checksum_file.exists()
        content = checksum_file.read_text()
        assert checksum in content
        assert "test.txt" in content

def test_scan_and_log_checksums():
    """Test scanning directory and logging checksums."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        checksum_file = data_dir / "checksums.txt"

        # Create test files
        (data_dir / "file1.txt").write_text("content1")
        (data_dir / "file2.txt").write_text("content2")
        subdir = data_dir / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("content3")

        logged = scan_and_log_checksums(data_dir, checksum_file)

        assert len(logged) == 3
        filenames = [path for path, _ in logged]
        assert "file1.txt" in filenames
        assert "file2.txt" in filenames
        assert "subdir/file3.txt" in filenames

        # Verify checksums.txt content
        assert checksum_file.exists()
        content = checksum_file.read_text()
        assert "SHA-256" in content  # Header comment
        assert len(content.strip().split("\n")) == 4  # Header + 3 files
