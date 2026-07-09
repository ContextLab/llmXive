"""
Unit tests for the hashing utilities.
"""
import os
import tempfile
from pathlib import Path

import pytest

from code.utils.hashing import compute_sha256, hash_directory_contents


def test_compute_sha256_empty_file():
    """Test hashing an empty file."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b'')
        temp_path = f.name

    try:
        # SHA256 of empty string is e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        result = compute_sha256(temp_path)
        assert result == expected
    finally:
        os.unlink(temp_path)


def test_compute_sha256_known_string():
    """Test hashing a known string."""
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
        f.write("hello world")
        temp_path = f.name

    try:
        # SHA256 of "hello world"
        expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        result = compute_sha256(temp_path)
        assert result == expected
    finally:
        os.unlink(temp_path)


def test_compute_sha256_file_not_found():
    """Test that FileNotFoundError is raised for missing files."""
    with pytest.raises(FileNotFoundError):
        compute_sha256("/nonexistent/path/file.txt")


def test_compute_sha256_directory():
    """Test that IsADirectoryError is raised for directories."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with pytest.raises(IsADirectoryError):
            compute_sha256(temp_dir)


def test_hash_directory_contents():
    """Test hashing all contents of a directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        # Create files
        (root / "file1.txt").write_text("content1")
        (root / "file2.txt").write_text("content2")
        subdir = root / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("content3")

        hashes = hash_directory_contents(root)

        assert len(hashes) == 3
        assert "file1.txt" in hashes
        assert "file2.txt" in hashes
        assert "subdir/file3.txt" in hashes


def test_hash_directory_ignore_patterns():
    """Test that ignore patterns work correctly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        (root / "file1.txt").write_text("content1")
        (root / "file.pyc").write_text("compiled")
        (root / "__pycache__").mkdir()
        (root / "__pycache__" / "cache.txt").write_text("cache")

        # Ignore .pyc and __pycache__
        hashes = hash_directory_contents(root, ignore_patterns=['*.pyc', '__pycache__'])

        assert len(hashes) == 1
        assert "file1.txt" in hashes
        assert "file.pyc" not in hashes
        assert "__pycache__/cache.txt" not in hashes