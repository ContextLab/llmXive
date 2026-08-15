"""
Unit tests for the checksum verification module.
"""
import json
import tempfile
import pytest
from pathlib import Path
from code.analysis.checksum_verifier import (
    calculate_file_checksum,
    load_checksum_manifest,
    verify_checksums
)

def test_calculate_file_checksum():
    """Test checksum calculation for a simple file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello, World!")
        temp_path = Path(f.name)
    
    try:
        checksum = calculate_file_checksum(temp_path)
        # SHA256 of "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert checksum == expected
    finally:
        temp_path.unlink()

def test_calculate_file_checksum_not_found():
    """Test that FileNotFoundError is raised for non-existent file."""
    with pytest.raises(FileNotFoundError):
        calculate_file_checksum(Path("/nonexistent/file.txt"))

def test_load_checksum_manifest():
    """Test loading a valid checksum manifest."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = Path(tmpdir) / "checksums.json"
        manifest_data = {
            "checksums": {
                "file1.txt": "abc123",
                "file2.txt": "def456"
            }
        }
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f)
        
        result = load_checksum_manifest(manifest_path)
        assert result == {"file1.txt": "abc123", "file2.txt": "def456"}

def test_load_checksum_manifest_not_found():
    """Test that FileNotFoundError is raised for non-existent manifest."""
    with pytest.raises(FileNotFoundError):
        load_checksum_manifest(Path("/nonexistent/manifest.json"))

def test_verify_checksums_all_pass():
    """Test verification when all checksums match."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create a test file
        test_file = tmpdir_path / "test.txt"
        test_file.write_text("Test content")
        
        # Calculate its checksum
        checksum = calculate_file_checksum(test_file)
        
        # Create manifest
        manifest_path = tmpdir_path / "checksums.json"
        manifest_data = {
            "checksums": {
                "test.txt": checksum
            }
        }
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f)
        
        # Verify
        all_passed, results = verify_checksums(manifest_path, tmpdir_path)
        
        assert all_passed is True
        assert len(results) == 1
        assert results[0]['passed'] is True
        assert results[0]['file'] == str(test_file)

def test_verify_checksums_mismatch():
    """Test verification when checksums don't match."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create a test file
        test_file = tmpdir_path / "test.txt"
        test_file.write_text("Test content")
        
        # Create manifest with wrong checksum
        manifest_path = tmpdir_path / "checksums.json"
        manifest_data = {
            "checksums": {
                "test.txt": "wrong_checksum"
            }
        }
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f)
        
        # Verify
        all_passed, results = verify_checksums(manifest_path, tmpdir_path)
        
        assert all_passed is False
        assert len(results) == 1
        assert results[0]['passed'] is False
        assert results[0]['actual'] is not None
        assert results[0]['actual'] != "wrong_checksum"

def test_verify_checksums_file_not_found():
    """Test verification when a file is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create manifest referencing non-existent file
        manifest_path = tmpdir_path / "checksums.json"
        manifest_data = {
            "checksums": {
                "nonexistent.txt": "some_checksum"
            }
        }
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f)
        
        # Verify
        all_passed, results = verify_checksums(manifest_path, tmpdir_path)
        
        assert all_passed is False
        assert len(results) == 1
        assert results[0]['passed'] is False
        assert results[0]['error'] == 'File not found'