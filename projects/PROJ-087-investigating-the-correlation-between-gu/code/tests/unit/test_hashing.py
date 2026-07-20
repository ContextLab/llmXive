import os
import tempfile
import pytest
from pathlib import Path
import hashlib

from src.utils.hashing import compute_sha256


def test_compute_sha256_known_file():
    """Test hashing a file with known content."""
    test_content = b"Hello, World! This is a test file for hashing."
    expected_hash = hashlib.sha256(test_content).hexdigest()

    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(test_content)
        tmp_path = tmp_file.name

    try:
        result = compute_sha256(tmp_path)
        assert result == expected_hash
    finally:
        os.unlink(tmp_path)


def test_compute_sha256_empty_file():
    """Test hashing an empty file."""
    empty_hash = hashlib.sha256(b"").hexdigest()

    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_path = tmp_file.name

    try:
        result = compute_sha256(tmp_path)
        assert result == empty_hash
    finally:
        os.unlink(tmp_path)


def test_compute_sha256_large_file_chunked():
    """Test hashing a larger file to ensure chunked reading works."""
    # Generate 1MB of data
    large_content = b"0" * (1024 * 1024)
    expected_hash = hashlib.sha256(large_content).hexdigest()

    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(large_content)
        tmp_path = tmp_file.name

    try:
        result = compute_sha256(tmp_path)
        assert result == expected_hash
    finally:
        os.unlink(tmp_path)


def test_compute_sha256_file_not_found():
    """Test that FileNotFoundError is raised for missing files."""
    with pytest.raises(FileNotFoundError):
        compute_sha256("/nonexistent/path/to/file.txt")


def test_compute_sha256_is_directory():
    """Test that IsADirectoryError is raised when path is a directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        with pytest.raises(IsADirectoryError):
            compute_sha256(tmp_dir)