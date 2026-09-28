"""
Unit tests for the checksums module.
"""

import os
import sys
import json
import hashlib
import tempfile
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.checksums import compute_sha256, store_data_checksum, verify_data_checksum, verify_submissions_integrity
from utils.helpers import get_project_root

def test_compute_sha256():
    """Test SHA-256 computation on a known string."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test data")
        temp_path = f.name

    try:
        checksum = compute_sha256(temp_path)
        expected = hashlib.sha256(b"test data").hexdigest()
        assert checksum == expected
    finally:
        os.unlink(temp_path)

def test_store_and_verify_checksum():
    """Test storing and verifying a checksum."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("col1,col2\nval1,val2")
        temp_path = f.name

    try:
        # Store checksum
        store_data_checksum(temp_path)

        # Verify checksum
        is_valid, current, stored = verify_data_checksum(temp_path)
        assert is_valid is True
        assert current == stored

        # Modify file
        with open(temp_path, 'w') as f:
            f.write("col1,col2\nval3,val4")

        # Verify should fail now
        is_valid, current, stored = verify_data_checksum(temp_path)
        assert is_valid is False
        assert current != stored
    finally:
        os.unlink(temp_path)

def test_missing_file():
    """Test handling of missing file."""
    with pytest.raises(FileNotFoundError):
        compute_sha256("/nonexistent/path/file.csv")

    with pytest.raises(FileNotFoundError):
        verify_submissions_integrity() # Assuming default path doesn't exist in test env without setup