import os
import json
import tempfile
import hashlib
from pathlib import Path
import pytest

from code.utils.hash import calculate_sha256, generate_manifest, verify_manifest

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_file(temp_dir):
    file_path = temp_dir / "test_file.txt"
    content = b"Hello, World! This is a test file for hashing."
    file_path.write_bytes(content)
    return file_path

def test_calculate_sha256(sample_file):
    """Test that calculate_sha256 returns the correct hash."""
    expected_hash = hashlib.sha256(sample_file.read_bytes()).hexdigest()
    actual_hash = calculate_sha256(sample_file)
    assert actual_hash == expected_hash

def test_calculate_sha256_nonexistent():
    """Test that calculate_sha256 raises FileNotFoundError for missing files."""
    with pytest.raises(FileNotFoundError):
        calculate_sha256("nonexistent_file.txt")

def test_calculate_sha256_directory(temp_dir):
    """Test that calculate_sha256 raises IsADirectoryError for directories."""
    with pytest.raises(IsADirectoryError):
        calculate_sha256(temp_dir)

def test_generate_manifest(temp_dir, sample_file):
    """Test that generate_manifest creates a valid JSON file."""
    manifest_path = temp_dir / "manifest.json"
    manifest = generate_manifest([sample_file], manifest_path)

    assert manifest_path.exists()
    assert "files" in manifest
    assert sample_file.name in manifest["files"]
    assert "sha256" in manifest["files"][sample_file.name]

def test_generate_manifest_writes_file(temp_dir, sample_file):
    """Test that generate_manifest actually writes to disk."""
    manifest_path = temp_dir / "output_manifest.json"
    generate_manifest([sample_file], manifest_path)
    assert manifest_path.stat().st_size > 0

def test_verify_manifest_success(temp_dir, sample_file):
    """Test verify_manifest returns True for valid files."""
    manifest_path = temp_dir / "manifest.json"
    generate_manifest([sample_file], manifest_path)

    assert verify_manifest(manifest_path) is True

def test_verify_manifest_failure(temp_dir, sample_file):
    """Test verify_manifest returns False if file is modified."""
    manifest_path = temp_dir / "manifest.json"
    generate_manifest([sample_file], manifest_path)

    # Modify the file
    sample_file.write_bytes(b"Modified content")

    assert verify_manifest(manifest_path) is False

def test_verify_manifest_missing_file(temp_dir, sample_file):
    """Test verify_manifest returns False if a file is missing."""
    manifest_path = temp_dir / "manifest.json"
    generate_manifest([sample_file], manifest_path)

    # Delete the file
    sample_file.unlink()

    assert verify_manifest(manifest_path) is False

def test_generate_manifest_with_extensions(temp_dir):
    """Test manifest generation with multiple files."""
    file1 = temp_dir / "data1.tsv"
    file1.write_text("col1\tcol2\n1\t2")
    file2 = temp_dir / "data2.bam"
    file2.write_bytes(b"BAM_HEADER_MOCK")

    manifest_path = temp_dir / "multi_manifest.json"
    manifest = generate_manifest([file1, file2], manifest_path)

    assert len(manifest["files"]) == 2
    assert file1.name in manifest["files"]
    assert file2.name in manifest["files"]

def test_generate_manifest_exclude_patterns(temp_dir):
    """Test that exclude_patterns works in generate_manifest."""
    file1 = temp_dir / "keep.tsv"
    file1.write_text("data")
    file2 = temp_dir / "temp.log"
    file2.write_text("log data")

    manifest_path = temp_dir / "filtered_manifest.json"
    manifest = generate_manifest(
        [file1, file2],
        manifest_path,
        exclude_patterns=["*.log"]
    )

    assert len(manifest["files"]) == 1
    assert file1.name in manifest["files"]
    assert file2.name not in manifest["files"]

def test_verify_manifest_invalid_json(temp_dir):
    """Test verify_manifest handles invalid JSON gracefully."""
    manifest_path = temp_dir / "bad_manifest.json"
    manifest_path.write_text("not valid json {")

    assert verify_manifest(manifest_path) is False

def test_verify_manifest_directory_not_found(temp_dir):
    """Test verify_manifest handles missing files in manifest."""
    manifest_path = temp_dir / "missing_manifest.json"
    manifest = {
        "files": {
            "nonexistent_file.txt": {"sha256": "abc123"}
        }
    }
    manifest_path.write_text(json.dumps(manifest))

    assert verify_manifest(manifest_path) is False
