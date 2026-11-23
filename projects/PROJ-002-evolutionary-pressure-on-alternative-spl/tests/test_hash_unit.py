"""
Unit tests for the artifact hashing utilities (T006).

Verifies:
- SHA-256 calculation for single files.
- Manifest generation.
- Manifest verification.
- Error handling for missing files and directories.
"""
import os
import json
import tempfile
import hashlib
from pathlib import Path
import pytest
from code.utils.hash import calculate_sha256, generate_manifest, verify_manifest

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_file(temp_dir):
    """Create a sample file with known content."""
    file_path = temp_dir / "test_file.txt"
    content = "Hello, World! This is a test file for hashing."
    file_path.write_text(content)
    return file_path

def test_calculate_sha256(sample_file):
    """Test SHA-256 calculation matches known value."""
    content = "Hello, World! This is a test file for hashing."
    expected_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
    actual_hash = calculate_sha256(sample_file)
    assert actual_hash == expected_hash

def test_calculate_sha256_nonexistent(temp_dir):
    """Test that hashing a non-existent file raises FileNotFoundError."""
    missing_path = temp_dir / "does_not_exist.txt"
    with pytest.raises(FileNotFoundError):
        calculate_sha256(missing_path)

def test_calculate_sha256_directory(temp_dir):
    """Test that hashing a directory raises IsADirectoryError."""
    with pytest.raises(IsADirectoryError):
        calculate_sha256(temp_dir)

def test_generate_manifest(temp_dir):
    """Test manifest generation creates correct JSON structure."""
    file1 = temp_dir / "file1.txt"
    file2 = temp_dir / "file2.txt"
    file1.write_text("content1")
    file2.write_text("content2")
    
    manifest_path = temp_dir / "manifest.json"
    manifest = generate_manifest([file1, file2], manifest_path)
    
    assert manifest["algorithm"] == "sha256"
    assert "generated_at" in manifest
    assert str(file1) in manifest["files"]
    assert str(file2) in manifest["files"]
    
    # Verify file existence
    assert manifest_path.exists()

def test_generate_manifest_writes_file(temp_dir):
    """Test that generate_manifest actually writes the file to disk."""
    file1 = temp_dir / "file1.txt"
    file1.write_text("content1")
    
    manifest_path = temp_dir / "manifest.json"
    generate_manifest([file1], manifest_path)
    
    assert manifest_path.exists()
    with open(manifest_path, 'r') as f:
        data = json.load(f)
    assert str(file1) in data["files"]

def test_verify_manifest_success(temp_dir):
    """Test successful verification of a valid manifest."""
    file1 = temp_dir / "file1.txt"
    file1.write_text("content1")
    
    manifest_path = temp_dir / "manifest.json"
    generate_manifest([file1], manifest_path)
    
    assert verify_manifest(manifest_path) is True

def test_verify_manifest_failure(temp_dir):
    """Test verification fails when file content changes."""
    file1 = temp_dir / "file1.txt"
    file1.write_text("content1")
    
    manifest_path = temp_dir / "manifest.json"
    generate_manifest([file1], manifest_path)
    
    # Modify file
    file1.write_text("content modified")
    
    assert verify_manifest(manifest_path) is False

def test_verify_manifest_missing_file(temp_dir):
    """Test verification fails when a file in manifest is missing."""
    file1 = temp_dir / "file1.txt"
    file1.write_text("content1")
    
    manifest_path = temp_dir / "manifest.json"
    generate_manifest([file1], manifest_path)
    
    # Delete file
    file1.unlink()
    
    assert verify_manifest(manifest_path) is False

def test_generate_manifest_with_extensions(temp_dir):
    """Test manifest generation with various file extensions."""
    files = [
        temp_dir / "test.bam",
        temp_dir / "results.tsv",
        temp_dir / "data.csv"
    ]
    for f in files:
        f.write_text("dummy content")
    
    manifest_path = temp_dir / "manifest.json"
    manifest = generate_manifest(files, manifest_path)
    
    assert len(manifest["files"]) == 3

def test_generate_manifest_exclude_patterns(temp_dir):
    """Test that exclude patterns work correctly."""
    file1 = temp_dir / "keep.txt"
    file2 = temp_dir / "skip.tmp"
    file1.write_text("keep")
    file2.write_text("skip")
    
    manifest_path = temp_dir / "manifest.json"
    manifest = generate_manifest(
        [file1, file2], 
        manifest_path, 
        exclude_patterns=["*.tmp"]
    )
    
    assert str(file1) in manifest["files"]
    assert str(file2) not in manifest["files"]

def test_verify_manifest_invalid_json(temp_dir):
    """Test verification fails on invalid JSON."""
    manifest_path = temp_dir / "invalid.json"
    manifest_path.write_text("not json")
    
    with pytest.raises(json.JSONDecodeError):
        verify_manifest(manifest_path)

def test_verify_manifest_directory_not_found(temp_dir):
    """Test verification handles missing manifest file."""
    missing_path = temp_dir / "missing.json"
    with pytest.raises(FileNotFoundError):
        verify_manifest(missing_path)
