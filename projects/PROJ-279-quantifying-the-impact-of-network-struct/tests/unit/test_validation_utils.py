"""
Unit tests for validation_utils module.

Tests checksum verification and file integrity checks.
"""
import pytest
import tempfile
import os
from pathlib import Path
import json
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from validation_utils import (
    compute_file_checksum,
    verify_file_integrity,
    create_manifest,
    verify_manifest,
    check_file_age,
    save_manifest
)
from logging_config import setup_logging

@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file with known content."""
    file_path = tmp_path / "test_file.txt"
    content = "This is test content for checksum verification."
    file_path.write_text(content)
    return file_path

@pytest.fixture
def temp_directory(tmp_path):
    """Create a temporary directory with test files."""
    # Create some test files
    (tmp_path / "file1.json").write_text('{"key": "value1"}')
    (tmp_path / "file2.json").write_text('{"key": "value2"}')
    (tmp_path / "file3.txt").write_text("Some text content")
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "nested.json").write_text('{"nested": true}')
    return tmp_path

def test_compute_file_checksum(temp_file):
    """Test SHA256 checksum computation."""
    checksum1 = compute_file_checksum(temp_file)
    checksum2 = compute_file_checksum(temp_file)
    
    # Checksums should be consistent
    assert checksum1 == checksum2
    
    # Checksum should be a valid hex string
    assert len(checksum1) == 64  # SHA256 produces 64 hex characters
    assert all(c in '0123456789abcdef' for c in checksum1)

def test_compute_file_checksum_nonexistent():
    """Test checksum computation on non-existent file."""
    with pytest.raises(FileNotFoundError):
        compute_file_checksum(Path("/nonexistent/file.txt"))

def test_verify_file_integrity_success(temp_file):
    """Test successful file integrity verification."""
    checksum = compute_file_checksum(temp_file)
    assert verify_file_integrity(temp_file, checksum) is True

def test_verify_file_integrity_failure(temp_file):
    """Test failed file integrity verification."""
    checksum = compute_file_checksum(temp_file)
    wrong_checksum = "a" * 64  # Invalid checksum
    assert verify_file_integrity(temp_file, wrong_checksum) is False

def test_verify_file_integrity_with_actual_checksum(temp_file):
    """Test verification with pre-computed checksum."""
    actual_checksum = compute_file_checksum(temp_file)
    assert verify_file_integrity(temp_file, actual_checksum, actual_checksum) is True

def test_create_manifest(temp_directory):
    """Test manifest creation."""
    manifest = create_manifest(temp_directory)
    
    # Should find all files
    assert len(manifest) == 4  # file1.json, file2.json, file3.txt, subdir/nested.json
    
    # All values should be valid checksums
    for checksum in manifest.values():
        assert len(checksum) == 64
        assert all(c in '0123456789abcdef' for c in checksum)

def test_create_manifest_with_patterns(temp_directory):
    """Test manifest creation with file patterns."""
    # Only include JSON files
    manifest = create_manifest(temp_directory, patterns=['*.json'])
    
    # Should find only JSON files
    assert len(manifest) == 3  # file1.json, file2.json, subdir/nested.json
    
    # No .txt files
    for path in manifest.keys():
        assert not path.endswith('.txt')

def test_verify_manifest_success(temp_directory):
    """Test successful manifest verification."""
    manifest = create_manifest(temp_directory)
    manifest_path = temp_directory / "manifest.json"
    save_manifest(manifest, manifest_path)
    
    is_valid, failures = verify_manifest(manifest_path)
    
    assert is_valid is True
    assert len(failures) == 0

def test_verify_manifest_file_missing(temp_directory):
    """Test manifest verification with missing file."""
    manifest = create_manifest(temp_directory)
    manifest_path = temp_directory / "manifest.json"
    save_manifest(manifest, manifest_path)
    
    # Delete a file
    (temp_directory / "file1.json").unlink()
    
    is_valid, failures = verify_manifest(manifest_path)
    
    assert is_valid is False
    assert "file1.json" in failures
    assert "not found" in failures["file1.json"].lower()

def test_verify_manifest_checksum_mismatch(temp_directory):
    """Test manifest verification with checksum mismatch."""
    manifest = create_manifest(temp_directory)
    manifest_path = temp_directory / "manifest.json"
    save_manifest(manifest, manifest_path)
    
    # Modify a file
    (temp_directory / "file1.json").write_text("Modified content")
    
    is_valid, failures = verify_manifest(manifest_path)
    
    assert is_valid is False
    assert "file1.json" in failures
    assert "mismatch" in failures["file1.json"].lower()

def test_check_file_age_fresh(temp_file):
    """Test file age check for fresh file."""
    # File should be fresh (just created)
    assert check_file_age(temp_file, max_age_hours=1.0) is True

def test_check_file_age_old(temp_file):
    """Test file age check for old file."""
    # Set file modification time to 24 hours ago
    old_time = os.path.getmtime(temp_file) - (24 * 3600)
    os.utime(temp_file, (old_time, old_time))
    
    # Should be old
    assert check_file_age(temp_file, max_age_hours=1.0) is False

def test_check_file_age_nonexistent():
    """Test file age check for non-existent file."""
    assert check_file_age(Path("/nonexistent/file.txt"), max_age_hours=1.0) is False

def test_save_manifest(tmp_path):
    """Test saving manifest to file."""
    manifest = {
        "file1.txt": "abc123...",
        "file2.txt": "def456..."
    }
    output_path = tmp_path / "test_manifest.json"
    saved_path = save_manifest(manifest, output_path)
    
    assert saved_path.exists()
    assert saved_path == output_path
    
    # Verify content
    with open(saved_path, 'r') as f:
        loaded_manifest = json.load(f)
    
    assert loaded_manifest == manifest

if __name__ == "__main__":
    pytest.main([__file__, "-v"])