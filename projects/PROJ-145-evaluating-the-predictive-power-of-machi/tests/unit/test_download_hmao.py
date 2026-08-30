"""
Unit tests for download_hmao.py (T017a).
Tests the checksum logic and file handling.
"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import hashlib

# Import the module functions
# We need to import the functions from the code module
# Since we are in tests/unit, we assume code/ is in the path or we import relative to project root
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.download_hmao import compute_file_checksum, get_dataset_checksum

def test_compute_file_checksum():
    """Test that compute_file_checksum returns the correct SHA256 for a known file."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        content = b"Hello, World!"
        tmp.write(content)
        tmp_path = Path(tmp.name)
    
    try:
        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = compute_file_checksum(tmp_path)
        assert actual_hash == expected_hash
    finally:
        os.unlink(tmp_path)

def test_compute_file_checksum_empty():
    """Test checksum for an empty file."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = Path(tmp.name)
    
    try:
        expected_hash = hashlib.sha256(b"").hexdigest()
        actual_hash = compute_file_checksum(tmp_path)
        assert actual_hash == expected_hash
    finally:
        os.unlink(tmp_path)

@patch('code.download_hmao.datasets.get_dataset_config_info')
def test_get_dataset_checksum_found(mock_get_info):
    """Test get_dataset_checksum when checksum is found in metadata."""
    mock_info = MagicMock()
    mock_info.download_checksums = {"data.parquet": "abc123"}
    mock_get_info.return_value = mock_info
    
    result = get_dataset_checksum()
    assert result == "abc123"

@patch('code.download_hmao.datasets.get_dataset_config_info')
def test_get_dataset_checksum_not_found(mock_get_info):
    """Test get_dataset_checksum when checksum is not found."""
    mock_info = MagicMock()
    mock_info.download_checksums = {}
    mock_get_info.return_value = mock_info
    
    result = get_dataset_checksum()
    assert result == "unknown"

@patch('code.download_hmao.datasets.get_dataset_config_info')
def test_get_dataset_checksum_exception(mock_get_info):
    """Test get_dataset_checksum when metadata fetch fails."""
    mock_get_info.side_effect = Exception("Network error")
    
    result = get_dataset_checksum()
    assert result == "unknown"
