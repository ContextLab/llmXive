"""
Unit tests for the hash utilities module.
"""
import os
import json
import tempfile
import hashlib
from pathlib import Path
import pytest

from code.utils.hash import calculate_sha256, generate_manifest, verify_manifest


def test_calculate_sha256():
    """Test SHA-256 calculation on a known string."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("Hello, World!")
        temp_path = f.name

    try:
        # Calculate expected hash manually
        expected_hash = hashlib.sha256(b"Hello, World!").hexdigest()
        actual_hash = calculate_sha256(temp_path)
        assert actual_hash == expected_hash
    finally:
        os.unlink(temp_path)


def test_calculate_sha256_nonexistent():
    """Test that FileNotFoundError is raised for missing files."""
    with pytest.raises(FileNotFoundError):
        calculate_sha256("/nonexistent/path/file.txt")


def test_calculate_sha256_directory():
    """Test that IsADirectoryError is raised for directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(IsADirectoryError):
            calculate_sha256(tmpdir)


def test_generate_manifest():
    """Test manifest generation for a list of files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        file1 = Path(tmpdir) / "file1.txt"
        file2 = Path(tmpdir) / "file2.txt"
        file1.write_text("Content 1")
        file2.write_text("Content 2")

        file_paths = [file1, file2]
        manifest = generate_manifest(file_paths, base_dir=tmpdir)

        assert len(manifest) == 2
        assert "file1.txt" in manifest
        assert "file2.txt" in manifest

        # Verify hashes manually
        hash1 = hashlib.sha256(b"Content 1").hexdigest()
        hash2 = hashlib.sha256(b"Content 2").hexdigest()
        assert manifest["file1.txt"] == hash1
        assert manifest["file2.txt"] == hash2


def test_generate_manifest_writes_file():
    """Test that generate_manifest writes to output_path if provided."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.txt"
        file_path.write_text("Test content")

        manifest_path = Path(tmpdir) / "manifest.json"
        generate_manifest([file_path], output_path=manifest_path, base_dir=tmpdir)

        assert manifest_path.exists()
        with open(manifest_path, "r") as f:
            data = json.load(f)
        assert "test.txt" in data


def test_verify_manifest_success():
    """Test successful verification."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "data.txt"
        file_path.write_text("Data for verification")

        # Create manifest
        manifest = {"data.txt": hashlib.sha256(b"Data for verification").hexdigest()}
        manifest_file = Path(tmpdir) / "manifest.json"
        with open(manifest_file, "w") as f:
            json.dump(manifest, f)

        assert verify_manifest(manifest_file, base_dir=tmpdir) is True


def test_verify_manifest_failure():
    """Test verification failure when file content changes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "data.txt"
        original_content = "Original content"
        file_path.write_text(original_content)

        # Create manifest with original hash
        original_hash = hashlib.sha256(original_content.encode()).hexdigest()
        manifest = {"data.txt": original_hash}
        manifest_file = Path(tmpdir) / "manifest.json"
        with open(manifest_file, "w") as f:
            json.dump(manifest, f)

        # Modify file
        file_path.write_text("Modified content")

        assert verify_manifest(manifest_file, base_dir=tmpdir) is False


def test_verify_manifest_missing_file():
    """Test verification failure when file is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest = {"missing.txt": "some_hash"}
        manifest_file = Path(tmpdir) / "manifest.json"
        with open(manifest_file, "w") as f:
            json.dump(manifest, f)

        assert verify_manifest(manifest_file, base_dir=tmpdir) is False