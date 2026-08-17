"""
Tests for code/utils/checksum.py
"""

import os
import tempfile
import hashlib

from code.utils.checksum import (
    compute_file_checksum,
    verify_file_checksum,
    write_checksum_file,
    read_checksum_file,
)


def test_compute_file_checksum():
    """Test checksum computation."""
    content = b"Hello, World! This is a test file."
    expected_hash = hashlib.sha256(content).hexdigest()

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        computed = compute_file_checksum(tmp_path)
        assert computed == expected_hash
    finally:
        os.remove(tmp_path)


def test_compute_file_checksum_not_found():
    """Test that compute_file_checksum raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        compute_file_checksum("/nonexistent/file.txt")


def test_verify_file_checksum_valid():
    """Test verification with a valid checksum."""
    content = b"Test data for verification."
    expected_hash = hashlib.sha256(content).hexdigest()

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        is_valid, _ = verify_file_checksum(tmp_path, expected_hash)
        assert is_valid is True
    finally:
        os.remove(tmp_path)


def test_verify_file_checksum_invalid():
    """Test verification with an invalid checksum."""
    content = b"Test data."
    wrong_hash = "0" * 64  # Invalid hash

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        is_valid, _ = verify_file_checksum(tmp_path, wrong_hash)
        assert is_valid is False
    finally:
        os.remove(tmp_path)


def test_write_and_read_checksum_file():
    """Test writing and reading a checksum file."""
    content = b"Content for checksum file test."

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        tmp.write(content)
        file_path = tmp.name

    checksum_path = file_path + ".checksum"

    try:
        write_checksum_file(file_path, checksum_path)
        algorithm, stored_hash = read_checksum_file(checksum_path)

        assert algorithm == "sha256"
        expected_hash = hashlib.sha256(content).hexdigest()
        assert stored_hash == expected_hash
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(checksum_path):
            os.remove(checksum_path)
