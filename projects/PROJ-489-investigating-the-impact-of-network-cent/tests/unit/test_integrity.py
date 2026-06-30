"""
Unit tests for the integrity check utility (code/integrity.py).
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

import sys
# Ensure code/ is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.integrity import (
    calculate_file_checksum,
    generate_manifest,
    verify_manifest,
    DEFAULT_MANIFEST_NAME
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory with dummy data files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data" / "raw"
        data_dir.mkdir(parents=True)
        
        # Create dummy files
        file1 = data_dir / "subject_01.edf"
        file1.write_text("dummy edf content 1")
        
        file2 = data_dir / "subject_02.edf"
        file2.write_text("dummy edf content 2")
        
        sub_dir = data_dir / "subfolder"
        sub_dir.mkdir()
        file3 = sub_dir / "subject_03.edf"
        file3.write_text("dummy edf content 3")

        yield data_dir

def test_calculate_file_checksum_sha256():
    """Test SHA256 checksum calculation."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test content")
        tmp_path = Path(tmp.name)
    
    try:
        checksum = calculate_file_checksum(tmp_path, "sha256")
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA256 hex length
    finally:
        tmp_path.unlink()

def test_calculate_file_checksum_md5():
    """Test MD5 checksum calculation."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test content")
        tmp_path = Path(tmp.name)
    
    try:
        checksum = calculate_file_checksum(tmp_path, "md5")
        assert isinstance(checksum, str)
        assert len(checksum) == 32  # MD5 hex length
    finally:
        tmp_path.unlink()

def test_calculate_file_checksum_invalid_algo():
    """Test that invalid algorithm raises ValueError."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = Path(tmp.name)
    
    try:
        with pytest.raises(ValueError, match="Unsupported algorithm"):
            calculate_file_checksum(tmp_path, "invalid_algo")
    finally:
        tmp_path.unlink()

def test_calculate_file_checksum_not_found():
    """Test that missing file raises FileNotFoundError."""
    fake_path = Path("/nonexistent/file.txt")
    with pytest.raises(FileNotFoundError):
        calculate_file_checksum(fake_path)

def test_generate_manifest(temp_data_dir):
    """Test manifest generation."""
    output_path = temp_data_dir.parent / "results" / "test_manifest.json"
    
    manifest = generate_manifest(temp_data_dir, output_path)
    
    assert "algorithm" in manifest
    assert manifest["algorithm"] == "sha256"
    assert "files" in manifest
    assert len(manifest["files"]) == 3  # 3 files created
    
    # Check file entries
    assert "subject_01.edf" in manifest["files"]
    assert "subfolder/subject_03.edf" in manifest["files"]
    
    # Check file content
    entry = manifest["files"]["subject_01.edf"]
    assert "checksum" in entry
    assert "size_bytes" in entry
    assert entry["size_bytes"] > 0

def test_verify_manifest_valid(temp_data_dir):
    """Test verification of valid files."""
    output_path = temp_data_dir.parent / "results" / "test_manifest.json"
    generate_manifest(temp_data_dir, output_path)
    
    is_valid, details = verify_manifest(temp_data_dir, output_path)
    
    assert is_valid is True
    assert len(details["valid_files"]) == 3
    assert len(details["invalid_files"]) == 0
    assert len(details["missing_files"]) == 0

def test_verify_manifest_corrupted(temp_data_dir):
    """Test verification with a corrupted file."""
    output_path = temp_data_dir.parent / "results" / "test_manifest.json"
    generate_manifest(temp_data_dir, output_path)
    
    # Corrupt a file
    file_path = temp_data_dir / "subject_01.edf"
    file_path.write_text("corrupted content")
    
    is_valid, details = verify_manifest(temp_data_dir, output_path)
    
    assert is_valid is False
    assert len(details["invalid_files"]) == 1
    assert "subject_01.edf" in details["invalid_files"]

def test_verify_manifest_missing_file(temp_data_dir):
    """Test verification with a missing file."""
    output_path = temp_data_dir.parent / "results" / "test_manifest.json"
    generate_manifest(temp_data_dir, output_path)
    
    # Delete a file
    file_path = temp_data_dir / "subject_01.edf"
    file_path.unlink()
    
    is_valid, details = verify_manifest(temp_data_dir, output_path)
    
    assert is_valid is False
    assert len(details["missing_files"]) == 1
    assert "subject_01.edf" in details["missing_files"]

def test_verify_manifest_new_file(temp_data_dir):
    """Test verification with a new file not in manifest."""
    output_path = temp_data_dir.parent / "results" / "test_manifest.json"
    generate_manifest(temp_data_dir, output_path)
    
    # Add a new file
    new_file = temp_data_dir / "subject_04.edf"
    new_file.write_text("new content")
    
    is_valid, details = verify_manifest(temp_data_dir, output_path)
    
    # Note: New files do not make the check invalid unless strict=True is enforced
    # The function returns is_valid=True if existing manifest files match, 
    # but reports new files in details.
    assert len(details["new_files"]) == 1
    assert "subject_04.edf" in details["new_files"]
    
    # By default, is_valid is True if all expected files are valid
    assert is_valid is True

def test_verify_manifest_strict_new_file(temp_data_dir):
    """Test verification with new file in strict mode."""
    output_path = temp_data_dir.parent / "results" / "test_manifest.json"
    generate_manifest(temp_data_dir, output_path)
    
    # Add a new file
    new_file = temp_data_dir / "subject_04.edf"
    new_file.write_text("new content")
    
    is_valid, details = verify_manifest(temp_data_dir, output_path, strict=True)
    
    # In strict mode, new files should trigger a failure
    assert is_valid is False
    assert len(details["new_files"]) == 1
