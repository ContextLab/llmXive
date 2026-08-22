"""
Unit tests for the artifact hashing utilities.
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
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_file(temp_dir):
    """Create a sample file with known content."""
    file_path = temp_dir / "test_file.txt"
    content = "Hello, World!"
    file_path.write_text(content)
    return file_path

def test_calculate_sha256(sample_file):
    """Test SHA-256 calculation on a known file."""
    content = "Hello, World!"
    expected_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    actual_hash = calculate_sha256(sample_file)
    assert actual_hash == expected_hash

def test_calculate_sha256_nonexistent():
    """Test that calculating hash of non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        calculate_sha256(Path("/nonexistent/file.txt"))

def test_calculate_sha256_directory(temp_dir):
    """Test that calculating hash of a directory raises IsADirectoryError."""
    with pytest.raises(IsADirectoryError):
        calculate_sha256(temp_dir)

def test_generate_manifest(temp_dir):
    """Test manifest generation."""
    # Create test files
    (temp_dir / "file1.txt").write_text("content1")
    (temp_dir / "file2.tsv").write_text("content2")
    (temp_dir / "subdir").mkdir()
    (temp_dir / "subdir" / "file3.bam").write_text("content3")
    
    manifest = generate_manifest(temp_dir)
    
    assert "files" in manifest
    assert "algorithm" in manifest
    assert manifest["algorithm"] == "sha256"
    assert len(manifest["files"]) == 3
    assert "file1.txt" in manifest["files"]
    assert "file2.tsv" in manifest["files"]
    assert "subdir/file3.bam" in manifest["files"]

def test_generate_manifest_writes_file(temp_dir):
    """Test that manifest generation can write to a file."""
    (temp_dir / "test.txt").write_text("test content")
    manifest_path = temp_dir / "manifest.json"
    
    generate_manifest(temp_dir, output_path=manifest_path)
    
    assert manifest_path.exists()
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    assert "files" in manifest
    assert len(manifest["files"]) == 1

def test_verify_manifest_success(temp_dir):
    """Test successful manifest verification."""
    # Create files and manifest
    (temp_dir / "file1.txt").write_text("content1")
    (temp_dir / "file2.txt").write_text("content2")
    
    manifest = generate_manifest(temp_dir)
    manifest_path = temp_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f)
    
    results = verify_manifest(manifest_path, temp_dir)
    
    assert results["valid"] is True
    assert results["verified_count"] == 2
    assert results["failed_count"] == 0
    assert results["missing_count"] == 0

def test_verify_manifest_failure(temp_dir):
    """Test manifest verification with hash mismatch."""
    # Create file and manifest
    file_path = temp_dir / "file1.txt"
    file_path.write_text("original content")
    
    manifest = generate_manifest(temp_dir)
    manifest_path = temp_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f)
    
    # Modify file content
    file_path.write_text("modified content")
    
    results = verify_manifest(manifest_path, temp_dir)
    
    assert results["valid"] is False
    assert results["verified_count"] == 0
    assert results["failed_count"] == 1
    assert results["missing_count"] == 0

def test_verify_manifest_missing_file(temp_dir):
    """Test manifest verification with missing file."""
    # Create file and manifest
    file_path = temp_dir / "file1.txt"
    file_path.write_text("content")
    
    manifest = generate_manifest(temp_dir)
    manifest_path = temp_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f)
    
    # Delete file
    file_path.unlink()
    
    results = verify_manifest(manifest_path, temp_dir)
    
    assert results["valid"] is False
    assert results["verified_count"] == 0
    assert results["failed_count"] == 0
    assert results["missing_count"] == 1

def test_generate_manifest_with_extensions(temp_dir):
    """Test manifest generation with extension filter."""
    (temp_dir / "file1.txt").write_text("content1")
    (temp_dir / "file2.tsv").write_text("content2")
    (temp_dir / "file3.bam").write_text("content3")
    
    manifest = generate_manifest(temp_dir, extensions=[".tsv", ".bam"])
    
    assert len(manifest["files"]) == 2
    assert "file1.txt" not in manifest["files"]
    assert "file2.tsv" in manifest["files"]
    assert "file3.bam" in manifest["files"]

def test_generate_manifest_exclude_patterns(temp_dir):
    """Test manifest generation with exclude patterns."""
    (temp_dir / "file1.txt").write_text("content1")
    (temp_dir / "pipeline.log").write_text("log content")
    (temp_dir / ".hidden").write_text("hidden content")
    
    manifest = generate_manifest(temp_dir, exclude_patterns=["*.log", ".*"])
    
    assert len(manifest["files"]) == 1
    assert "file1.txt" in manifest["files"]
    assert "pipeline.log" not in manifest["files"]
    assert ".hidden" not in manifest["files"]

def test_verify_manifest_invalid_json(temp_dir):
    """Test verification with invalid JSON manifest."""
    manifest_path = temp_dir / "manifest.json"
    manifest_path.write_text("not valid json")
    
    with pytest.raises(json.JSONDecodeError):
        verify_manifest(manifest_path, temp_dir)

def test_verify_manifest_directory_not_found():
    """Test verification when base directory is not found."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = Path(tmpdir) / "manifest.json"
        manifest_path.write_text('{"algorithm": "sha256", "directory": "/nonexistent", "files": {}}')
        
        with pytest.raises(FileNotFoundError):
            verify_manifest(manifest_path, Path("/nonexistent"))
