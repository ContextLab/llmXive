"""
Unit tests for the hasher module.

Tests cover:
- File hash computation
- Directory hash computation
- Manifest save/load operations
- Artifact verification
- Edge cases and error handling
"""

import hashlib
import json
import os
import tempfile
from pathlib import Path
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.hasher import (
    compute_file_hash,
    compute_directory_hash,
    save_hash_manifest,
    load_hash_manifest,
    verify_artifacts,
    generate_artifact_hash,
)


@pytest.fixture
def temp_file():
    """Create a temporary file with known content."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("test content")
        path = f.name
    yield path
    os.unlink(path)


@pytest.fixture
def temp_dir():
    """Create a temporary directory with test files."""
    tmpdir = tempfile.mkdtemp()
    dir_path = Path(tmpdir)
    
    # Create test files
    (dir_path / "file1.txt").write_text("content1")
    (dir_path / "file2.txt").write_text("content2")
    (dir_path / "subdir").mkdir()
    (dir_path / "subdir" / "file3.txt").write_text("content3")
    
    yield dir_path
    
    # Cleanup
    import shutil
    shutil.rmtree(tmpdir)


def test_compute_file_hash(temp_file):
    """Test that file hash is computed correctly."""
    # Known content: "test content"
    expected_hash = hashlib.sha256(b"test content").hexdigest()
    actual_hash = compute_file_hash(temp_file)
    assert actual_hash == expected_hash
    

def test_compute_file_hash_nonexistent():
    """Test that computing hash of non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        compute_file_hash("/nonexistent/path/file.txt")


def test_compute_directory_hash(temp_dir):
    """Test directory hash computation."""
    # Directory hash should be deterministic
    hash1 = compute_directory_hash(temp_dir)
    hash2 = compute_directory_hash(temp_dir)
    assert hash1 == hash2
    
    # Should be a valid hex string
    assert len(hash1) == 64  # SHA-256 hex length
    assert all(c in "0123456789abcdef" for c in hash1)


def test_compute_directory_hash_with_extension_filter(temp_dir):
    """Test directory hash with extension filter."""
    # Only include .txt files
    hash_txt = compute_directory_hash(temp_dir, include_extensions=[".txt"])
    
    # Should differ if we filter to non-existent extension
    hash_none = compute_directory_hash(temp_dir, include_extensions=[".xyz"])
    assert hash_txt != hash_none
    

def test_compute_directory_hash_with_exclude(temp_dir):
    """Test directory hash with exclude patterns."""
    # Hash all files
    hash_all = compute_directory_hash(temp_dir)
    
    # Exclude files containing "file2"
    hash_excluded = compute_directory_hash(temp_dir, exclude_patterns=["file2"])
    
    # Should be different
    assert hash_all != hash_excluded


def test_save_and_load_hash_manifest(temp_dir):
    """Test saving and loading hash manifests."""
    artifacts = {
        "file1.txt": "hash1",
        "file2.txt": "hash2",
    }
    
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        manifest_path = f.name
        
    try:
        # Save manifest
        save_hash_manifest(artifacts, manifest_path, {"test": "value"})
        
        # Load manifest
        loaded = load_hash_manifest(manifest_path)
        
        # Verify contents
        assert loaded["artifacts"] == artifacts
        assert loaded["metadata"]["test"] == "value"
        assert loaded["version"] == "1.0"
        assert loaded["algorithm"] == "sha256"
        
    finally:
        os.unlink(manifest_path)


def test_verify_artifacts_valid(temp_dir):
    """Test verification of valid artifacts."""
    # Create artifacts dict with correct hashes
    artifacts = {}
    for file_path in temp_dir.rglob("*.txt"):
        rel_path = str(file_path.relative_to(temp_dir))
        artifacts[rel_path] = compute_file_hash(file_path)
    
    results = verify_artifacts(artifacts, temp_dir)
    
    # All should be valid
    assert all(results.values())
    assert len(results) == len(artifacts)


def test_verify_artifacts_modified(temp_dir):
    """Test verification detects modified files."""
    # Get correct hash
    file_path = temp_dir / "file1.txt"
    correct_hash = compute_file_hash(file_path)
    
    artifacts = {
        "file1.txt": correct_hash,
    }
    
    # Modify file
    file_path.write_text("modified content")
    
    results = verify_artifacts(artifacts, temp_dir)
    
    # Should detect modification
    assert results["file1.txt"] == False


def test_verify_artifacts_missing(temp_dir):
    """Test verification detects missing files."""
    artifacts = {
        "nonexistent.txt": "somehash",
    }
    
    results = verify_artifacts(artifacts, temp_dir)
    
    # Should detect missing file
    assert results["nonexistent.txt"] == False


def test_generate_artifact_hash_string():
    """Test hash generation from string."""
    data = "test string"
    expected = hashlib.sha256(data.encode("utf-8")).hexdigest()
    actual = generate_artifact_hash(data)
    assert actual == expected


def test_generate_artifact_hash_bytes():
    """Test hash generation from bytes."""
    data = b"test bytes"
    expected = hashlib.sha256(data).hexdigest()
    actual = generate_artifact_hash(data)
    assert actual == expected


def test_generate_artifact_hash_empty():
    """Test hash generation from empty data."""
    expected = hashlib.sha256(b"").hexdigest()
    assert generate_artifact_hash("") == expected
    assert generate_artifact_hash(b"") == expected