"""
Unit tests for src/utils/checksums.py
"""

import hashlib
import os
import tempfile
from pathlib import Path

import pytest

from src.utils.checksums import compute_sha256, verify_checksum, generate_checksum_file


def test_compute_sha256():
    """Test SHA256 computation on a known string."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        content = b"Hello, World!"
        f.write(content)
        temp_path = f.name

    try:
        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = compute_sha256(temp_path)
        assert actual_hash == expected_hash
    finally:
        os.unlink(temp_path)


def test_verify_checksum_success():
    """Test successful checksum verification."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        content = b"Test data"
        f.write(content)
        temp_path = f.name

    try:
        expected_hash = hashlib.sha256(content).hexdigest()
        is_valid, msg = verify_checksum(temp_path, expected_hash)
        assert is_valid is True
        assert "successful" in msg
    finally:
        os.unlink(temp_path)


def test_verify_checksum_failure():
    """Test checksum verification failure on mismatch."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"Test data")
        temp_path = f.name

    try:
        is_valid, msg = verify_checksum(temp_path, "invalid_hash")
        assert is_valid is False
        assert "mismatch" in msg
    finally:
        os.unlink(temp_path)


def test_generate_checksum_file():
    """Test generation of a .sha256 sidecar file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "data.txt"
        file_path.write_text("Content to checksum")

        checksum_path = generate_checksum_file(file_path, tmpdir)

        assert checksum_path.exists()
        assert checksum_path.name == "data.txt.sha256"

        with open(checksum_path, "r") as f:
            line = f.read()
            parts = line.split()
            assert len(parts) == 2
            assert parts[1] == "data.txt"

            # Verify the hash is correct
            expected_hash = hashlib.sha256(b"Content to checksum").hexdigest()
            assert parts[0] == expected_hash
