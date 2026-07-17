import pytest
import json
import tempfile
import os
from pathlib import Path
import hashlib

from data_generation.utils import compute_checksum
from data_checksum_manager import (
    create_directories,
    compute_file_checksum,
    record_checksums,
    save_checksums,
    load_checksums,
    verify_integrity
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        # Create standard data structure
        create_directories(str(root))
        yield root
        # Cleanup handled by TemporaryDirectory

def test_checksum_deterministic(temp_data_dir):
    """Test that checksums are deterministic for the same content."""
    test_file = temp_data_dir / "data" / "generated" / "test.txt"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    content = "test content for checksum verification"
    test_file.write_text(content)
    
    checksum1 = compute_file_checksum(test_file)
    checksum2 = compute_file_checksum(test_file)
    
    assert checksum1 == checksum2
    assert len(checksum1) == 64  # SHA256 hex length

def test_checksum_unique(temp_data_dir):
    """Test that different content produces different checksums."""
    test_file = temp_data_dir / "data" / "generated" / "test.txt"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    test_file.write_text("content A")
    checksum_a = compute_file_checksum(test_file)
    
    test_file.write_text("content B")
    checksum_b = compute_file_checksum(test_file)
    
    assert checksum_a != checksum_b

def test_record_checksums(temp_data_dir):
    """Test recording checksums for files."""
    # Create test files
    file1 = temp_data_dir / "data" / "generated" / "file1.txt"
    file2 = temp_data_dir / "data" / "models" / "file2.txt"
    
    file1.parent.mkdir(parents=True, exist_ok=True)
    file2.parent.mkdir(parents=True, exist_ok=True)
    
    file1.write_text("content 1")
    file2.write_text("content 2")
    
    checksums = record_checksums(temp_data_dir / "data")
    
    assert len(checksums) == 2
    paths = [c["path"] for c in checksums]
    assert any("file1.txt" in p for p in paths)
    assert any("file2.txt" in p for p in paths)

def test_save_load_checksums(temp_data_dir):
    """Test saving and loading checksums."""
    # Create a test file
    test_file = temp_data_dir / "data" / "generated" / "test.txt"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("test content")
    
    # Record and save
    checksums = record_checksums(temp_data_dir / "data")
    output_path = temp_data_dir / "data" / "checksums.json"
    save_checksums(checksums, output_path)
    
    assert output_path.exists()
    
    # Load and verify
    loaded_checksums = load_checksums(output_path)
    assert len(loaded_checksums) == 1
    assert loaded_checksums[0]["path"] == "generated/test.txt"

def test_verify_integrity_success(temp_data_dir):
    """Test successful integrity verification."""
    # Create test files
    test_file = temp_data_dir / "data" / "generated" / "test.txt"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("test content")
    
    # Record and save checksums
    checksums = record_checksums(temp_data_dir / "data")
    output_path = temp_data_dir / "data" / "checksums.json"
    save_checksums(checksums, output_path)
    
    # Verify
    results = verify_integrity(temp_data_dir / "data", output_path)
    
    assert results["status"] == "success"
    assert results["verified"] == 1
    assert results["failed"] == 0
    assert results["missing"] == 0

def test_verify_integrity_missing_file(temp_data_dir):
    """Test integrity verification with missing files."""
    # Create and record checksums
    test_file = temp_data_dir / "data" / "generated" / "test.txt"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("test content")
    
    checksums = record_checksums(temp_data_dir / "data")
    output_path = temp_data_dir / "data" / "checksums.json"
    save_checksums(checksums, output_path)
    
    # Delete the file
    test_file.unlink()
    
    # Verify should fail
    results = verify_integrity(temp_data_dir / "data", output_path)
    
    assert results["status"] == "failed"
    assert results["missing"] == 1
    assert results["verified"] == 0

def test_verify_integrity_modified_file(temp_data_dir):
    """Test integrity verification with modified files."""
    # Create and record checksums
    test_file = temp_data_dir / "data" / "generated" / "test.txt"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("original content")
    
    checksums = record_checksums(temp_data_dir / "data")
    output_path = temp_data_dir / "data" / "checksums.json"
    save_checksums(checksums, output_path)
    
    # Modify the file
    test_file.write_text("modified content")
    
    # Verify should fail
    results = verify_integrity(temp_data_dir / "data", output_path)
    
    assert results["status"] == "failed"
    assert results["failed"] == 1
    assert results["verified"] == 0
