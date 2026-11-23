"""
Unit tests for checksum functionality.
"""
import pytest
import tempfile
import os
from preprocess import compute_checksum

def test_checksum_computation():
    """Test checksum computation for a file."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test data")
        temp_path = f.name
    
    try:
        checksum = compute_checksum(temp_path)
        assert checksum is not None
        assert len(checksum) == 64  # SHA-256 produces 64 hex characters
    finally:
        os.unlink(temp_path)
