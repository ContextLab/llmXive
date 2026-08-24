"""
Unit tests for the artifact hashing utilities (T006).
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
    file_path = temp_dir / "sample.txt"
    content = "Hello, World! This is a test file for hashing."
    file_path.write_text(content)
    return file_path


def test_calculate_sha256(sample_file):
    """Test that calculate_sha256 returns the correct hash."""
    content = sample_file.read_text()
    expected_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
    actual_hash = calculate_sha256(sample_file)
    assert actual_hash == expected_hash


def test_calculate_sha256_nonexistent(temp_dir):
    """Test that calculate_sha256 raises FileNotFoundError for missing files."""
    missing_path = temp_dir / "does_not_exist.txt"
    with pytest.raises(FileNotFoundError):
        calculate_sha256(missing_path)


def test_calculate_sha256_directory(temp_dir):
    """Test that calculate_sha256 raises IsADirectoryError for directories."""
    with pytest.raises(IsADirectoryError):
        calculate_sha256(temp_dir)


def test_generate_manifest(sample_file, temp_dir):
    """Test manifest generation without writing to disk."""
    manifest = generate_manifest([sample_file])
    assert "artifacts" in manifest
    assert str(sample_file) in manifest["artifacts"]
    assert len(manifest["artifacts"][str(sample_file)]) == 64  # SHA-256 hex length


def test_generate_manifest_writes_file(sample_file, temp_dir):
    """Test that generate_manifest writes the JSON file correctly."""
    output_path = temp_dir / "manifest.json"
    manifest = generate_manifest([sample_file], output_path)

    assert output_path.exists()
    with open(output_path, "r") as f:
        loaded_manifest = json.load(f)
    assert loaded_manifest == manifest


def test_verify_manifest_success(sample_file, temp_dir):
    """Test successful verification of a valid manifest."""
    output_path = temp_dir / "manifest.json"
    generate_manifest([sample_file], output_path)
    assert verify_manifest(output_path) is True


def test_verify_manifest_failure(sample_file, temp_dir):
    """Test verification fails when file content changes."""
    output_path = temp_dir / "manifest.json"
    generate_manifest([sample_file], output_path)

    # Modify the file
    sample_file.write_text("Modified content")

    assert verify_manifest(output_path) is False


def test_verify_manifest_missing_file(temp_dir):
    """Test verification fails when a file is missing."""
    # Create a manifest with a fake path
    fake_path = temp_dir / "missing.txt"
    manifest = {
        "version": "1.0",
        "algorithm": "sha256",
        "artifacts": {
            str(fake_path): "0000000000000000000000000000000000000000000000000000000000000000"
        },
        "external_artifacts": {}
    }
    output_path = temp_dir / "manifest.json"
    with open(output_path, "w") as f:
        json.dump(manifest, f)

    assert verify_manifest(output_path) is False


def test_generate_manifest_with_extensions(sample_file, temp_dir):
    """Test manifest generation with multiple files of different types."""
    txt_file = temp_dir / "test.txt"
    txt_file.write_text("Text content")
    bin_file = temp_dir / "test.bin"
    bin_file.write_bytes(b"\x00\x01\x02")

    output_path = temp_dir / "multi_manifest.json"
    manifest = generate_manifest([sample_file, txt_file, bin_file], output_path)

    assert len(manifest["artifacts"]) == 3
    assert verify_manifest(output_path) is True


def test_generate_manifest_exclude_patterns(sample_file, temp_dir):
    """Test that directories are skipped in manifest generation."""
    sub_dir = temp_dir / "subdir"
    sub_dir.mkdir()
    (sub_dir / "inside.txt").write_text("Inside")

    output_path = temp_dir / "dir_manifest.json"
    # Pass the directory path; it should be skipped per implementation
    manifest = generate_manifest([temp_dir, sample_file], output_path)

    # The directory should be skipped, only the file included
    assert len(manifest["artifacts"]) == 1
    assert str(sample_file) in manifest["artifacts"]


def test_verify_manifest_invalid_json(temp_dir):
    """Test that verify_manifest raises error on invalid JSON."""
    output_path = temp_dir / "bad_manifest.json"
    output_path.write_text("This is not JSON")

    with pytest.raises(json.JSONDecodeError):
        verify_manifest(output_path)


def test_verify_manifest_directory_not_found(temp_dir):
    """Test verification when a referenced directory path is missing."""
    missing_dir = temp_dir / "missing_dir"
    manifest = {
        "version": "1.0",
        "algorithm": "sha256",
        "artifacts": {
            str(missing_dir): "hashvalue"
        },
        "external_artifacts": {}
    }
    output_path = temp_dir / "manifest.json"
    with open(output_path, "w") as f:
        json.dump(manifest, f)

    # Should return False because file is missing, not raise FileNotFoundError
    # (Our implementation checks existence and logs error, returns False)
    assert verify_manifest(output_path) is False
