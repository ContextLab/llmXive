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
    content = b"Hello, World! This is a test file for hashing."
    file_path.write_bytes(content)
    return file_path

def test_calculate_sha256(sample_file):
    """Test that calculate_sha256 returns the correct hash for a known file."""
    content = sample_file.read_bytes()
    expected_hash = hashlib.sha256(content).hexdigest()
    actual_hash = calculate_sha256(sample_file)
    assert actual_hash == expected_hash
    assert len(actual_hash) == 64  # SHA-256 hex length

def test_calculate_sha256_nonexistent():
    """Test that calculate_sha256 raises FileNotFoundError for missing files."""
    with pytest.raises(FileNotFoundError):
        calculate_sha256(Path("/nonexistent/path/file.txt"))

def test_calculate_sha256_directory(temp_dir):
    """Test that calculate_sha256 raises IsADirectoryError for directories."""
    with pytest.raises(IsADirectoryError):
        calculate_sha256(temp_dir)

def test_generate_manifest(temp_dir):
    """Test generate_manifest creates correct hashes for multiple files."""
    file1 = temp_dir / "file1.txt"
    file2 = temp_dir / "file2.txt"
    
    content1 = b"Content 1"
    content2 = b"Content 2"
    
    file1.write_bytes(content1)
    file2.write_bytes(content2)

    manifest = generate_manifest([file1, file2])
    
    assert len(manifest) == 2
    assert file1.name in manifest
    assert file2.name in manifest
    
    expected_hash1 = hashlib.sha256(content1).hexdigest()
    expected_hash2 = hashlib.sha256(content2).hexdigest()
    
    assert manifest[file1.name] == expected_hash1
    assert manifest[file2.name] == expected_hash2

def test_generate_manifest_writes_file(temp_dir):
    """Test that generate_manifest writes to file if output_path is provided."""
    file1 = temp_dir / "file1.txt"
    file1.write_bytes(b"Test content")
    
    manifest_path = temp_dir / "manifest.json"
    
    generate_manifest([file1], output_path=manifest_path)
    
    assert manifest_path.exists()
    with open(manifest_path, "r") as f:
        loaded_manifest = json.load(f)
    
    assert file1.name in loaded_manifest
    assert loaded_manifest[file1.name] == hashlib.sha256(b"Test content").hexdigest()

def test_verify_manifest_success(temp_dir):
    """Test verify_manifest returns True when all files match."""
    file1 = temp_dir / "file1.txt"
    file1.write_bytes(b"Valid content")
    
    manifest_data = {
        "file1.txt": hashlib.sha256(b"Valid content").hexdigest()
    }
    manifest_path = temp_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest_data))
    
    assert verify_manifest(manifest_path) is True

def test_verify_manifest_failure(temp_dir):
    """Test verify_manifest returns False when hash mismatch occurs."""
    file1 = temp_dir / "file1.txt"
    file1.write_bytes(b"Changed content")
    
    manifest_data = {
        "file1.txt": hashlib.sha256(b"Original content").hexdigest()
    }
    manifest_path = temp_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest_data))
    
    assert verify_manifest(manifest_path) is False

def test_verify_manifest_missing_file(temp_dir):
    """Test verify_manifest returns False when a file is missing."""
    manifest_data = {
      "missing_file.txt": "some_hash_value"
    }
    manifest_path = temp_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest_data))
    
    assert verify_manifest(manifest_path) is False
