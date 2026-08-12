"""
tests/unit/test_checksum.py

Unit tests for code/utils/checksum.py
"""
import pytest
import tempfile
import os
from pathlib import Path
from code.utils.checksum import calculate_checksum, verify_checksum

def test_calculate_checksum_valid_file():
    """Test that calculate_checksum returns a valid SHA-256 hex string."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = f.name

    try:
        checksum = calculate_checksum(temp_path)
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA-256 hex length
        assert all(c in '0123456789abcdef' for c in checksum)
    finally:
        os.unlink(temp_path)

def test_verify_checksum_match():
    """Test verify_checksum returns True when checksum matches."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = f.name

    try:
        checksum = calculate_checksum(temp_path)
        assert verify_checksum(temp_path, checksum) is True
    finally:
        os.unlink(temp_path)

def test_verify_checksum_mismatch():
    """Test verify_checksum returns False when checksum does not match."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = f.name

    try:
        wrong_checksum = "a" * 64
        assert verify_checksum(temp_path, wrong_checksum) is False
    finally:
        os.unlink(temp_path)

def test_calculate_checksum_file_not_found():
    """Test that calculate_checksum raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        calculate_checksum("/nonexistent/path/file.json")
