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
    """Test that calculate_sha256 returns the correct hash."""
    expected_hash = hashlib.sha256(sample_file.read_bytes()).hexdigest()
    actual_hash = calculate_sha256(sample_file)
    assert actual_hash == expected_hash

def test_calculate_sha256_nonexistent(temp_dir):
    """Test that calculate_sha256 raises FileNotFoundError for missing files."""
    missing_file = temp_dir / "does_not_exist.txt"
    with pytest.raises(FileNotFoundError):
        calculate_sha256(missing_file)

def test_calculate_sha256_directory(temp_dir):
    """Test that calculate_sha256 raises IsADirectoryError for directories."""
    with pytest.raises(IsADirectoryError):
        calculate_sha256(temp_dir)

def test_generate_manifest(temp_dir, sample_file):
    """Test that generate_manifest creates a valid JSON manifest."""
    manifest_path = temp_dir / "manifest.json"
    result = generate_manifest([sample_file], manifest_path)
    
    assert result["algorithm"] == "sha256"
    assert str(sample_file) in result["files"]
    assert "hash" in result["files"][str(sample_file)]
    assert "size_bytes" in result["files"][str(sample_file)]
    
    # Verify file was written
    assert manifest_path.exists()
    with open(manifest_path) as f:
        loaded = json.load(f)
    assert loaded == result

def test_generate_manifest_writes_file(temp_dir, sample_file):
    """Test that generate_manifest writes to the specified output path."""
    manifest_path = temp_dir / "custom" / "subdir" / "output.json"
    generate_manifest([sample_file], manifest_path)
    assert manifest_path.exists()

def test_verify_manifest_success(temp_dir, sample_file):
    """Test verify_manifest returns True when hashes match."""
    manifest_path = temp_dir / "manifest.json"
    generate_manifest([sample_file], manifest_path)
    
    assert verify_manifest(manifest_path) is True

def test_verify_manifest_failure(temp_dir, sample_file):
    """Test verify_manifest returns False when file content changes."""
    manifest_path = temp_dir / "manifest.json"
    generate_manifest([sample_file], manifest_path)
    
    # Modify file content
    sample_file.write_text("Modified content")
    
    assert verify_manifest(manifest_path) is False

def test_verify_manifest_missing_file(temp_dir, sample_file):
    """Test verify_manifest returns False when a file is missing."""
    manifest_path = temp_dir / "manifest.json"
    generate_manifest([sample_file], manifest_path)
    
    # Delete the file
    sample_file.unlink()
    
    assert verify_manifest(manifest_path) is False

def test_generate_manifest_with_extensions(temp_dir):
    """Test manifest generation with multiple file types."""
    txt_file = temp_dir / "data.txt"
    txt_file.write_text("text")
    
    json_file = temp_dir / "data.json"
    json_file.write_text('{"key": "value"}')
    
    manifest_path = temp_dir / "multi_manifest.json"
    result = generate_manifest([txt_file, json_file], manifest_path)
    
    assert len(result["files"]) == 2

def test_verify_manifest_invalid_json(temp_dir):
    """Test verify_manifest raises error on invalid JSON."""
    manifest_path = temp_dir / "bad_manifest.json"
    manifest_path.write_text("not json")
    
    with pytest.raises(json.JSONDecodeError):
        verify_manifest(manifest_path)

def test_verify_manifest_directory_not_found(temp_dir):
    """Test verify_manifest handles missing base_dir correctly."""
    manifest_path = temp_dir / "manifest.json"
    file_path = temp_dir / "file.txt"
    file_path.write_text("content")
    
    generate_manifest([file_path], manifest_path)
    
    # Verify with a non-existent base_dir
    assert verify_manifest(manifest_path, base_dir=temp_dir / "non_existent") is False