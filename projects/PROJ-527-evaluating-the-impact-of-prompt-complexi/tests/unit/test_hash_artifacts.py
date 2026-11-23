"""
Unit tests for the artifact hashing utilities.
"""

import json
import tempfile
from pathlib import Path

import pytest

from utils.hash_artifacts import (
    calculate_sha256,
    hash_directory,
    verify_artifacts,
    create_manifest,
)


@pytest.fixture
def temp_file_structure(tmp_path):
    """Create a temporary directory structure with known content."""
    # Create subdirectories
    dir1 = tmp_path / "subdir1"
    dir2 = tmp_path / "subdir2"
    dir1.mkdir()
    dir2.mkdir()

    # Create files with known content
    file1 = tmp_path / "file1.txt"
    file1.write_text("Hello World")

    file2 = dir1 / "file2.txt"
    file2.write_text("Test Content")

    file3 = dir2 / "file3.json"
    file3.write_text('{"key": "value"}')

    return tmp_path, [file1, file2, file3]


def test_calculate_sha256_file_not_found():
    """Test that FileNotFoundError is raised for missing files."""
    with pytest.raises(FileNotFoundError):
        calculate_sha256("/nonexistent/path/file.txt")


def test_calculate_sha256_known_hash(temp_file_structure):
    """Test SHA256 calculation against a known value."""
    tmp_path, files = temp_file_structure
    file1 = files[0]

    # "Hello World" SHA256
    expected_hash = "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"
    actual_hash = calculate_sha256(file1)

    assert actual_hash == expected_hash


def test_hash_directory(temp_file_structure):
    """Test hashing all files in a directory."""
    tmp_path, files = temp_file_structure

    hashes = hash_directory(tmp_path)

    assert len(hashes) == 3
    assert "file1.txt" in hashes
    assert "subdir1/file2.txt" in hashes
    assert "subdir2/file3.json" in hashes


def test_hash_directory_with_extension_filter(temp_file_structure):
    """Test hashing only specific file extensions."""
    tmp_path, files = temp_file_structure

    hashes = hash_directory(tmp_path, extensions=[".txt"])

    assert len(hashes) == 2
    assert "file1.txt" in hashes
    assert "subdir1/file2.txt" in hashes
    assert "subdir2/file3.json" not in hashes


def test_hash_directory_with_exclude_dirs(temp_file_structure):
    """Test excluding specific directories."""
    tmp_path, files = temp_file_structure

    hashes = hash_directory(tmp_path, exclude_dirs=["subdir2"])

    assert len(hashes) == 2
    assert "file1.txt" in hashes
    assert "subdir1/file2.txt" in hashes
    assert "subdir2/file3.json" not in hashes


def test_verify_artifacts_success(temp_file_structure):
    """Test successful verification against a valid manifest."""
    tmp_path, files = temp_file_structure

    # Create a manifest
    manifest_path = tmp_path / "manifest.json"
    hashes = hash_directory(tmp_path)
    with open(manifest_path, "w") as f:
        json.dump(hashes, f)

    # Verify
    assert verify_artifacts(manifest_path, tmp_path) is True


def test_verify_artifacts_missing_file(temp_file_structure):
    """Test verification fails when a file is missing."""
    tmp_path, files = temp_file_structure

    # Create a manifest
    manifest_path = tmp_path / "manifest.json"
    hashes = hash_directory(tmp_path)
    with open(manifest_path, "w") as f:
        json.dump(hashes, f)

    # Delete a file
    files[0].unlink()

    # Verify should return False
    assert verify_artifacts(manifest_path, tmp_path) is False


def test_verify_artifacts_hash_mismatch(temp_file_structure):
    """Test verification fails when hash does not match."""
    tmp_path, files = temp_file_structure

    # Create a manifest with a wrong hash
    manifest_path = tmp_path / "manifest.json"
    hashes = hash_directory(tmp_path)
    # Tamper with the hash of the first file
    first_file_key = "file1.txt"
    hashes[first_file_key] = "0" * 64

    with open(manifest_path, "w") as f:
        json.dump(hashes, f)

    # Verify should return False
    assert verify_artifacts(manifest_path, tmp_path) is False


def test_create_manifest(temp_file_structure):
    """Test creating a manifest file."""
    tmp_path, files = temp_file_structure
    output_path = tmp_path / "output_manifest.json"

    hashes = create_manifest(tmp_path, output_path)

    assert output_path.exists()
    assert len(hashes) == 3

    with open(output_path, "r") as f:
        loaded_hashes = json.load(f)

    assert loaded_hashes == hashes