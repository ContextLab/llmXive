"""
Unit tests for SHA-256 checksum verification logic.
"""
import hashlib
import tempfile
import os
from pathlib import Path

# Import the function to test from the actual implementation
# Note: Since the implementation file is in code/data/, we need to adjust imports
# This test assumes the code structure is available in the PYTHONPATH
import sys
from pathlib import Path

# Add the code directory to the path if running from tests/
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from data.verify_checksums import compute_sha256


def test_compute_sha256_known_value():
    """Test SHA-256 computation against a known string."""
    test_string = "hello world"
    expected_hash = hashlib.sha256(test_string.encode('utf-8')).hexdigest()
    actual_hash = compute_sha256(test_string)
    assert actual_hash == expected_hash, f"Expected {expected_hash}, got {actual_hash}"


def test_compute_sha256_file(tmp_path):
    """Test SHA-256 computation on a temporary file."""
    test_content = b"binary data test \x00\x01\x02"
    test_file = tmp_path / "test.bin"
    test_file.write_bytes(test_content)

    expected_hash = hashlib.sha256(test_content).hexdigest()
    actual_hash = compute_sha256(str(test_file))

    assert actual_hash == expected_hash, f"File hash mismatch: {actual_hash} != {expected_hash}"


def test_compute_sha256_empty_file(tmp_path):
    """Test SHA-256 on an empty file."""
    empty_file = tmp_path / "empty.txt"
    empty_file.touch()

    expected_hash = hashlib.sha256(b"").hexdigest()
    actual_hash = compute_sha256(str(empty_file))

    assert actual_hash == expected_hash
