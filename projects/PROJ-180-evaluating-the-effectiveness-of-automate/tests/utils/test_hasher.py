"""
Tests for the hasher module.
"""
import os
import json
import tempfile
from pathlib import Path
import pytest

# Import the module under test
# Assuming the test is run from project root, code is in code/utils/
try:
    from code.utils.hasher import (
        hash_file,
        hash_directory,
        verify_file_hash,
        generate_manifest,
        verify_manifest
    )
except ImportError:
    # Fallback for different import structures
    from code.utils import hasher
    hash_file = hasher.hash_file
    hash_directory = hasher.hash_directory
    verify_file_hash = hasher.verify_file_hash
    generate_manifest = hasher.generate_manifest
    verify_manifest = hasher.verify_manifest


@pytest.fixture
def temp_dir():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create nested structure
        (tmpdir / "file1.txt").write_text("Hello, World!")
        (tmpdir / "file2.txt").write_text("Test content")
        
        subdir = tmpdir / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("Nested file")
        
        # Create a file to exclude
        (tmpdir / "temp.pyc").write_text("Bytecode")
        
        yield tmpdir


def test_hash_file_simple():
    """Test hashing a simple file."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("Hello, World!")
        temp_path = f.name
    
    try:
        hash_result = hash_file(temp_path)
        assert len(hash_result) == 64  # SHA-256 hex length
        assert all(c in "0123456789abcdef" for c in hash_result)
    finally:
        os.unlink(temp_path)


def test_hash_file_not_found():
    """Test hashing a non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        hash_file("/nonexistent/path/file.txt")


def test_hash_file_different_content():
    """Test that different content produces different hashes."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f1:
        f1.write("Content A")
        path1 = f1.name
    
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f2:
        f2.write("Content B")
        path2 = f2.name
    
    try:
        hash1 = hash_file(path1)
        hash2 = hash_file(path2)
        assert hash1 != hash2
    finally:
        os.unlink(path1)
        os.unlink(path2)


def test_hash_directory(temp_dir):
    """Test hashing all files in a directory."""
    hashes = hash_directory(temp_dir, recursive=True)
    
    assert "file1.txt" in hashes
    assert "file2.txt" in hashes
    assert "subdir/file3.txt" in hashes
    assert len(hashes) == 3


def test_hash_directory_exclude_patterns(temp_dir):
    """Test excluding files by pattern."""
    hashes = hash_directory(temp_dir, recursive=True, exclude_patterns=["*.pyc"])
    
    assert "file1.txt" in hashes
    assert "temp.pyc" not in hashes
    assert len(hashes) == 3


def test_verify_file_hash_match():
    """Test verifying a file with correct hash."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("Test content")
        temp_path = f.name
    
    try:
        correct_hash = hash_file(temp_path)
        assert verify_file_hash(temp_path, correct_hash) is True
    finally:
        os.unlink(temp_path)


def test_verify_file_hash_mismatch():
    """Test verifying a file with incorrect hash."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("Test content")
        temp_path = f.name
    
    try:
        wrong_hash = "a" * 64
        assert verify_file_hash(temp_path, wrong_hash) is False
    finally:
        os.unlink(temp_path)


def test_generate_manifest(temp_dir):
    """Test generating a manifest file."""
    with tempfile.TemporaryDirectory() as out_dir:
        manifest_path = Path(out_dir) / "manifest.json"
        result = generate_manifest(temp_dir, output_path=manifest_path)
        
        assert result["file_count"] == 3
        assert "file1.txt" in result["files"]
        assert manifest_path.exists()
        
        # Verify the saved manifest
        with open(manifest_path) as f:
            saved_manifest = json.load(f)
        
        assert saved_manifest == result


def test_verify_manifest(temp_dir):
    """Test verifying files against a manifest."""
    with tempfile.TemporaryDirectory() as out_dir:
        manifest_path = Path(out_dir) / "manifest.json"
        generate_manifest(temp_dir, output_path=manifest_path)
        
        # All should pass initially
        results = verify_manifest(manifest_path)
        assert all(results.values())
        
        # Modify a file to cause failure
        file_to_modify = temp_dir / "file1.txt"
        file_to_modify.write_text("Modified content")
        
        results = verify_manifest(manifest_path)
        assert results["file1.txt"] is False
        assert results["file2.txt"] is True
        assert results["subdir/file3.txt"] is True


def test_hash_directory_nonexistent():
    """Test hashing a non-existent directory raises error."""
    with pytest.raises(NotADirectoryError):
        hash_directory("/nonexistent/directory")