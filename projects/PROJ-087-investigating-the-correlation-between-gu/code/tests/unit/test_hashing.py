"""
Unit tests for the hashing utility module.
"""
import os
import tempfile
import pytest
from pathlib import Path
import hashlib

from src.utils.hashing import compute_sha256


def test_compute_sha256_known_file():
    """Test SHA-256 computation on a file with known content."""
    expected_content = b"Hello, World!"
    expected_hash = hashlib.sha256(expected_content).hexdigest()

    with tempfile.NamedTemporaryFile(delete=False, mode="wb") as tmp:
        tmp.write(expected_content)
        tmp_path = tmp.name

    try:
        computed_hash = compute_sha256(tmp_path)
        assert computed_hash == expected_hash
    finally:
        os.unlink(tmp_path)


def test_compute_sha256_empty_file():
    """Test SHA-256 computation on an empty file."""
    expected_hash = hashlib.sha256(b"").hexdigest()

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        # File is created empty
        tmp_path = tmp.name

    try:
        computed_hash = compute_sha256(tmp_path)
        assert computed_hash == expected_hash
    finally:
        os.unlink(tmp_path)


def test_compute_sha256_large_file_chunked():
    """Test that large files are hashed correctly using chunked reading."""
    # Create a file with known repeated pattern
    chunk = b"0123456789" * 1000  # 10KB chunk
    num_chunks = 100  # 1MB total
    expected_content = chunk * num_chunks
    expected_hash = hashlib.sha256(expected_content).hexdigest()

    with tempfile.NamedTemporaryFile(delete=False, mode="wb") as tmp:
        tmp.write(expected_content)
        tmp_path = tmp.name

    try:
        computed_hash = compute_sha256(tmp_path)
        assert computed_hash == expected_hash
    finally:
        os.unlink(tmp_path)


def test_compute_sha256_file_not_found():
    """Test that FileNotFoundError is raised for non-existent file."""
    with pytest.raises(FileNotFoundError):
        compute_sha256("/nonexistent/path/to/file.txt")


def test_compute_sha256_is_directory():
    """Test that IsADirectoryError is raised when path is a directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(IsADirectoryError):
            compute_sha256(tmpdir)