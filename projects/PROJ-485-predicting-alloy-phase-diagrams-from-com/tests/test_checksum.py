"""
Unit tests for checksum utilities.
"""
import os
import tempfile
import pytest

from code.utils.checksum import compute_file_sha256, verify_file_checksum, compute_and_store_checksum


def test_compute_file_sha256_valid_file():
    """Test computing checksum of a valid file."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test data for checksum")
        tmp_path = tmp.name

    try:
        checksum = compute_file_sha256(tmp_path)
        assert checksum is not None
        assert len(checksum) == 64  # SHA-256 hex length
        assert all(c in '0123456789abcdef' for c in checksum)
    finally:
        os.unlink(tmp_path)


def test_compute_file_sha256_nonexistent_file():
    """Test computing checksum of a non-existent file returns None."""
    checksum = compute_file_sha256("/nonexistent/path/file.txt")
    assert checksum is None


def test_verify_file_checksum_match():
    """Test verification when checksum matches."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test data for checksum")
        tmp_path = tmp.name

    try:
        actual_checksum = compute_file_sha256(tmp_path)
        assert verify_file_checksum(tmp_path, actual_checksum) is True
    finally:
        os.unlink(tmp_path)


def test_verify_file_checksum_mismatch():
    """Test verification when checksum does not match."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test data for checksum")
        tmp_path = tmp.name

    try:
        assert verify_file_checksum(tmp_path, "0" * 64) is False
    finally:
        os.unlink(tmp_path)


def test_compute_and_store_checksum():
    """Test computing and storing checksum to a file."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test data for checksum")
        tmp_path = tmp.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".sha256") as out:
        out_path = out.name

    try:
        success, checksum = compute_and_store_checksum(tmp_path, out_path)
        assert success is True
        assert len(checksum) == 64

        # Verify file content
        with open(out_path, "r") as f:
            content = f.read().strip()
        assert content.startswith(checksum)
        assert os.path.basename(tmp_path) in content
    finally:
        os.unlink(tmp_path)
        os.unlink(out_path)


def test_compute_and_store_checksum_no_output_path():
    """Test computing checksum without storing to file."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test data for checksum")
        tmp_path = tmp.name

    try:
        success, checksum = compute_and_store_checksum(tmp_path)
        assert success is True
        assert len(checksum) == 64
    finally:
        os.unlink(tmp_path)
