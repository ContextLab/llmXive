"""
Unit tests for checksums.py (Task T012e).
"""
import json
import os
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# We need to mock get_path and ensure_dirs to avoid dependency on full project config
# during unit testing, or ensure the test environment has them.
# For this test, we will patch the config/utils imports.

@pytest.fixture
def temp_raw_dir():
    """Create a temporary directory with dummy files for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create dummy files
        file1 = tmp_path / "test_file1.zip"
        file1.write_bytes(b"dummy content 1")
        
        file2 = tmp_path / "test_file2.tar.gz"
        file2.write_bytes(b"dummy content 2")
        
        yield tmp_path

def test_compute_sha256(temp_raw_dir):
    """Test that compute_sha256 returns the correct hash for a file."""
    from checksums import compute_sha256
    
    filepath = temp_raw_dir / "test_file1.zip"
    expected_hash = hashlib.sha256(b"dummy content 1").hexdigest()
    
    result = compute_sha256(filepath)
    assert result == expected_hash

def test_compute_sha256_missing_file():
    """Test that compute_sha256 raises FileNotFoundError for missing file."""
    from checksums import compute_sha256
    
    with tempfile.TemporaryDirectory() as tmpdir:
        missing_path = Path(tmpdir) / "nonexistent.zip"
        
        with pytest.raises(FileNotFoundError):
            compute_sha256(missing_path)

@patch('checksums.get_path')
@patch('checksums.ensure_dirs')
def test_record_checksums(mock_ensure_dirs, mock_get_path, temp_raw_dir):
    """Test that record_checksums writes the correct JSON structure."""
    from checksums import record_checksums
    
    mock_get_path.return_value = temp_raw_dir
    
    filenames = ["test_file1.zip", "test_file2.tar.gz"]
    record_checksums(temp_raw_dir, filenames)
    
    output_path = temp_raw_dir / "checksums.json"
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        data = json.load(f)
    
    assert len(data) == 2
    # Check structure
    for entry in data:
        assert "filename" in entry
        assert "sha256" in entry
        assert len(entry["sha256"]) == 64 # SHA-256 hex length

@patch('checksums.get_path')
@patch('checksums.ensure_dirs')
def test_main_no_files(mock_ensure_dirs, mock_get_path):
    """Test main() behavior when no archive files are found."""
    from checksums import main
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Create a non-archive file
        (tmp_path / "readme.txt").write_text("hello")
        
        mock_get_path.return_value = tmp_path
        
        main()
        
        # Should create an empty checksums.json
        output_path = tmp_path / "checksums.json"
        assert output_path.exists()
        with open(output_path, "r") as f:
            data = json.load(f)
        assert data == []
