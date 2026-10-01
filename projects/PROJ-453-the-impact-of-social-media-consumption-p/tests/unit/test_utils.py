"""
Unit tests for utility functions.
"""
import pytest
from utils import checksum_file, causal_language_scanner
import tempfile
import os

def test_checksum_file_valid():
    """Test checksum calculation on a valid file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = f.name
    
    try:
        checksum = checksum_file(temp_path)
        assert len(checksum) == 64
    finally:
        os.unlink(temp_path)

def test_checksum_file_not_found():
    """Test checksum calculation on a non-existent file."""
    with pytest.raises(FileNotFoundError):
        checksum_file("nonexistent_file_12345.txt")

def test_causal_language_scanner_positive():
    """Test scanner detects forbidden words."""
    assert causal_language_scanner("X causes Y", ["causes"]) is True
    assert causal_language_scanner("X leads to Y", ["leads to"]) is True
    assert causal_language_scanner("X impacts Y", ["impacts"]) is True

def test_causal_language_scanner_negative():
    """Test scanner allows non-forbidden words."""
    assert causal_language_scanner("X is associated with Y", ["causes"]) is False
    assert causal_language_scanner("X correlates with Y", ["causes"]) is False

def test_causal_language_scanner_case_insensitive():
    """Test scanner is case insensitive."""
    assert causal_language_scanner("X CAUSES Y", ["causes"]) is True
    assert causal_language_scanner("X Causes Y", ["causes"]) is True
