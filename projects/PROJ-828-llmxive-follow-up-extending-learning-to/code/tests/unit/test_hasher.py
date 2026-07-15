"""
Unit tests for src.utils.hasher module.
"""
import hashlib
import json
import os
import tempfile
from pathlib import Path
import pytest

# Adjust path for imports when running from test directory
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from src.utils.hasher import (
    compute_file_hash,
    compute_directory_hash,
    save_hash_manifest,
    load_hash_manifest,
    verify_artifacts,
    generate_artifact_hash
)

@pytest.fixture
def temp_file():
    """Create a temporary file with known content."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello, World!")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_dir():
    """Create a temporary directory with some files."""
    temp_path = tempfile.mkdtemp()
    
    # Create some files
    Path(temp_path, "file1.txt").write_text("Content 1")
    Path(temp_path, "file2.txt").write_text("Content 2")
    Path(temp_path, "data.bin").write_bytes(b"\x00\x01\x02\x03")
    
    # Create a subdirectory with a file
    subdir = Path(temp_path, "subdir")
    subdir.mkdir()
    Path(subdir, "nested.txt").write_text("Nested content")
    
    # Create a file to exclude
    Path(temp_path, "exclude.tmp").write_text("Should be excluded")
    
    yield temp_path
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_path)

def test_compute_file_hash(temp_file):
    """Test SHA-256 hash of a single file."""
    # Expected hash of "Hello, World!"
    expected = hashlib.sha256(b"Hello, World!").hexdigest()
    result = compute_file_hash(temp_file)
    assert result == expected
    assert len(result) == 64  # SHA-256 hex length

def test_compute_file_hash_nonexistent():
    """Test error handling for non-existent file."""
    with pytest.raises(FileNotFoundError):
        compute_file_hash("/nonexistent/path/file.txt")

def test_compute_directory_hash(temp_dir):
    """Test hashing all files in a directory."""
    hashes = compute_directory_hash(temp_dir)
    
    # Should have 4 files (file1.txt, file2.txt, data.bin, nested.txt)
    assert len(hashes) == 4
    
    # Verify specific files exist
    assert "file1.txt" in hashes
    assert "file2.txt" in hashes
    assert "data.bin" in hashes
    assert "subdir/nested.txt" in hashes or "subdir\\nested.txt" in hashes

def test_compute_directory_hash_with_extension_filter(temp_dir):
    """Test hashing only specific file extensions."""
    hashes = compute_directory_hash(temp_dir, extensions=[".txt"])
    
    # Should have 3 txt files
    assert len(hashes) == 3
    assert "data.bin" not in hashes

def test_compute_directory_hash_with_exclude(temp_dir):
    """Test excluding specific directories."""
    # Create a directory that should be excluded
    exclude_dir = Path(temp_dir, "__pycache__")
    exclude_dir.mkdir()
    Path(exclude_dir, "cache.bin").write_bytes(b"cache")
    
    hashes = compute_directory_hash(temp_dir)
    
    # __pycache__ should be excluded
    cache_files = [k for k in hashes.keys() if "__pycache__" in k]
    assert len(cache_files) == 0

def test_save_and_load_hash_manifest(temp_dir):
    """Test saving and loading a hash manifest."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        manifest_path = f.name
    
    try:
        hashes = compute_directory_hash(temp_dir)
        save_hash_manifest(hashes, manifest_path)
        
        # Verify file exists
        assert Path(manifest_path).exists()
        
        # Load and compare
        loaded = load_hash_manifest(manifest_path)
        assert loaded == hashes
        
        # Check JSON structure
        with open(manifest_path, 'r') as f:
            data = json.load(f)
        assert "algorithm" in data
        assert data["algorithm"] == "sha256"
        assert "files" in data
    finally:
        os.unlink(manifest_path)

def test_verify_artifacts_valid(temp_dir):
    """Test verifying artifacts that match their hashes."""
    hashes = compute_directory_hash(temp_dir)
    results = verify_artifacts(hashes, temp_dir)
    
    assert all(results.values())
    assert len(results) == len(hashes)

def test_verify_artifacts_modified(temp_dir):
    """Test verifying artifacts after modification."""
    hashes = compute_directory_hash(temp_dir)
    
    # Modify a file
    file_to_modify = Path(temp_dir, "file1.txt")
    file_to_modify.write_text("Modified content")
    
    results = verify_artifacts(hashes, temp_dir)
    
    # The modified file should fail verification
    assert results["file1.txt"] == False
    # Others should still pass
    assert results["file2.txt"] == True

def test_verify_artifacts_missing(temp_dir):
    """Test verifying when a file is missing."""
    hashes = compute_directory_hash(temp_dir)
    
    # Remove a file
    file_to_remove = Path(temp_dir, "file1.txt")
    file_to_remove.unlink()
    
    results = verify_artifacts(hashes, temp_dir)
    
    # The missing file should fail verification
    assert results["file1.txt"] == False

def test_generate_artifact_hash_string():
    """Test hashing string content."""
    content = "Test string"
    expected = hashlib.sha256(content.encode('utf-8')).hexdigest()
    result = generate_artifact_hash(content)
    assert result == expected

def test_generate_artifact_hash_bytes():
    """Test hashing bytes content."""
    content = b"Test bytes"
    expected = hashlib.sha256(content).hexdigest()
    result = generate_artifact_hash(content)
    assert result == expected

def test_generate_artifact_hash_empty():
    """Test hashing empty content."""
    expected = hashlib.sha256(b"").hexdigest()
    assert generate_artifact_hash("") == expected
    assert generate_artifact_hash(b"") == expected
