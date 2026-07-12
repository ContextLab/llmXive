"""
tests/test_download.py

Unit tests for the data download module.
Verifies that the download logic handles errors gracefully and
that the module structure is correct.
"""
import os
import sys
import pytest
from pathlib import Path

# Add project root to path if not already there
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.data.download import (
    calculate_file_hash,
    verify_checksums,
    DATASET_NAME,
    FALLBACK_DATASET
)

def test_calculate_file_hash(tmp_path):
    """Test that file hashing works correctly."""
    test_file = tmp_path / "test.txt"
    test_content = b"Hello, World!"
    test_file.write_bytes(test_content)
    
    hash_result = calculate_file_hash(test_file)
    assert len(hash_result) == 64  # SHA256 hex length
    assert isinstance(hash_result, str)

def test_verify_checksums_empty():
    """Test that verify_checksums returns False for empty list."""
    assert verify_checksums([]) is False

def test_verify_checksums_missing_file(tmp_path):
    """Test that verify_checksums handles missing files."""
    missing_file = tmp_path / "does_not_exist.txt"
    assert verify_checksums([missing_file]) is False

def test_verify_checksums_present_file(tmp_path):
    """Test that verify_checksums handles existing files."""
    test_file = tmp_path / "exists.txt"
    test_file.write_text("content")
    # Should return True if all files exist
    assert verify_checksums([test_file]) is True

def test_dataset_constants_defined():
    """Verify that dataset names are defined as expected."""
    assert isinstance(DATASET_NAME, str)
    assert len(DATASET_NAME) > 0
    assert isinstance(FALLBACK_DATASET, str)
    assert len(FALLBACK_DATASET) > 0

# Note: Integration test for actual download is skipped in unit tests 
# as it requires network access and time. It is covered by the 
# end-to-end pipeline script.
def test_import_structure():
    """Verify the module imports correctly."""
    import code.data.download as download_module
    assert hasattr(download_module, 'main')
    assert hasattr(download_module, 'download_dataset')