import os
import tempfile
import pytest
from pathlib import Path
import hashlib
from src.utils.hashing import compute_sha256


def test_compute_sha256_known_file():
    """Test hashing a file with a known content."""
    content = b"Hello, World!"
    expected_hash = hashlib.sha256(content).hexdigest()

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = compute_sha256(tmp_path)
        assert result == expected_hash
    finally:
        os.unlink(tmp_path)


def test_compute_sha256_empty_file():
    """Test hashing an empty file."""
    expected_hash = hashlib.sha256(b"").hexdigest()

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name

    try:
        result = compute_sha256(tmp_path)
        assert result == expected_hash
    finally:
        os.unlink(tmp_path)


def test_compute_sha256_large_file_chunked():
    """Test hashing a large file to ensure chunked reading works."""
    # Create a file larger than the default chunk size (64KB)
    chunk_size = 65536
    num_chunks = 100
    content = b"A" * chunk_size * num_chunks
    expected_hash = hashlib.sha256(content).hexdigest()

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = compute_sha256(tmp_path)
        assert result == expected_hash
    finally:
        os.unlink(tmp_path)


def test_compute_sha256_file_not_found():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        compute_sha256("/nonexistent/path/to/file.txt")


def test_compute_sha256_is_directory():
    """Test that IsADirectoryError is raised when path is a directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        with pytest.raises(IsADirectoryError):
            compute_sha256(tmp_dir)