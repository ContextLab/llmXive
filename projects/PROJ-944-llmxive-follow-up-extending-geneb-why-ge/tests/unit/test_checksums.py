"""
Unit tests for the checksum generation utility.
"""
import os
import tempfile
from pathlib import Path
import hashlib
import pytest

# Import the module to test
# We need to adjust the import path if running tests from root
# Assuming the test runner adds project root to sys.path
import sys
from pathlib import Path

# Add project root to path if not already there
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.utils.checksums import compute_sha256, scan_directory_for_hashes

def test_compute_sha256():
    """Test SHA-256 computation on a known string."""
    content = b"Hello, World!"
    expected_hash = hashlib.sha256(content).hexdigest()

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        computed_hash = compute_sha256(tmp_path)
        assert computed_hash == expected_hash
    finally:
        os.unlink(tmp_path)

def test_scan_directory_for_hashes():
    """Test scanning a directory for file hashes."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create some test files
        (tmp_path / "file1.txt").write_text("Content 1")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file2.txt").write_text("Content 2")

        # Compute expected hashes
        expected_hashes = {
            "file1.txt": hashlib.sha256(b"Content 1").hexdigest(),
            "subdir/file2.txt": hashlib.sha256(b"Content 2").hexdigest()
        }

        # Run the scan
        result = scan_directory_for_hashes(tmp_path)

        assert result == expected_hashes

def test_scan_empty_directory():
    """Test scanning an empty directory returns empty dict."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        result = scan_directory_for_hashes(tmp_path)
        assert result == {}

def test_scan_nonexistent_directory():
    """Test scanning a nonexistent directory returns empty dict."""
    fake_path = Path("/nonexistent/path/12345")
    result = scan_directory_for_hashes(fake_path)
    assert result == {}
