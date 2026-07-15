"""
Unit tests for the checksumming logic in code/utils.py.
Verifies SHA-256 computation for real files.
"""
import os
import tempfile
import pytest
from pathlib import Path

# Import the function under test
from code.utils import compute_file_checksum


def test_sha256_known_value():
    """
    Test SHA-256 checksum against a known string value.
    Input: "hello world" -> Expected SHA-256: b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9
    """
    content = b"hello world"
    expected_hash = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        file_path = Path(tmp_path)
        result = compute_file_checksum(file_path)
        assert result == expected_hash, f"Checksum mismatch: {result} != {expected_hash}"
    finally:
        os.unlink(tmp_path)


def test_sha256_empty_file():
    """Test SHA-256 checksum of an empty file."""
    content = b""
    expected_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        file_path = Path(tmp_path)
        result = compute_file_checksum(file_path)
        assert result == expected_hash, f"Checksum mismatch for empty file: {result} != {expected_hash}"
    finally:
        os.unlink(tmp_path)


def test_file_not_found():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        compute_file_checksum(Path("non_existent_file_12345.txt"))


def test_invalid_algorithm():
    """Test that ValueError is raised for unsupported algorithm."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test")
        tmp_path = tmp.name
    
    try:
        file_path = Path(tmp_path)
        with pytest.raises(ValueError, match="Algorithm 'invalid_algo' not available"):
            compute_file_checksum(file_path, algorithm="invalid_algo")
    finally:
        os.unlink(tmp_path)


def test_large_file_chunking():
    """Test checksum calculation on a larger file to ensure chunking works."""
    # Create a 1MB file
    content = b"X" * (1024 * 1024)
    
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        file_path = Path(tmp_path)
        # Just verify it runs without error and returns a 64-char hex string (SHA-256)
        result = compute_file_checksum(file_path)
        assert len(result) == 64, f"SHA-256 result should be 64 chars, got {len(result)}"
        assert all(c in '0123456789abcdef' for c in result), "Result should be valid hex"
    finally:
        os.unlink(tmp_path)