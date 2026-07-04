"""
Unit tests for checksum generation.
"""
import pytest
import tempfile
import os
from pathlib import Path
from src.utils.checksum import (
    generate_checksum,
    generate_checksum_from_bytes,
    generate_checksum_from_dict
)


def test_file_checksum():
    """Test checksum generation for a file."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test data")
        temp_path = f.name

    try:
        checksum = generate_checksum(temp_path)
        assert len(checksum) == 64  # SHA256 hex length
        assert isinstance(checksum, str)
    finally:
        os.unlink(temp_path)


def test_file_not_found():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        generate_checksum("nonexistent_file.txt")


def test_bytes_checksum():
    """Test checksum generation from bytes."""
    data = b"test data"
    checksum = generate_checksum_from_bytes(data)
    assert len(checksum) == 64
    assert isinstance(checksum, str)


def test_dict_checksum():
    """Test checksum generation from dictionary."""
    data = {"key": "value", "number": 123}
    checksum = generate_checksum_from_dict(data)
    assert len(checksum) == 64
    assert isinstance(checksum, str)


def test_dict_canonicalization():
    """Test that dict checksum is consistent regardless of key order."""
    data1 = {"key": "value", "number": 123}
    data2 = {"number": 123, "key": "value"}
    
    checksum1 = generate_checksum_from_dict(data1)
    checksum2 = generate_checksum_from_dict(data2)
    
    assert checksum1 == checksum2


def test_unsupported_algorithm():
    """Test that ValueError is raised for unsupported algorithm."""
    with pytest.raises(ValueError):
        generate_checksum_from_bytes(b"data", algorithm="invalid_algo")