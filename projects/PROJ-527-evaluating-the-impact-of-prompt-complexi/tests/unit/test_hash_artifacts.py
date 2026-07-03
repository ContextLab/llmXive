"""
Unit tests for code/utils/hash_artifacts.py
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

# Import the module functions
# We assume the test is run from the project root or we adjust sys.path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from utils.hash_artifacts import (
    calculate_sha256,
    hash_directory,
    verify_artifacts,
    create_manifest,
)


def test_calculate_sha256():
    """Test SHA-256 calculation on a known string."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("Hello, World!")
        temp_path = f.name

    try:
        # Known SHA-256 for "Hello, World!"
        expected_hash = "7f83b1657ff1fc53b92dc18148a1d65dfa34d0c7e2d039c33803290565957606"
        actual_hash = calculate_sha256(temp_path)
        assert actual_hash == expected_hash
    finally:
        os.unlink(temp_path)


def test_calculate_sha256_nonexistent():
    """Test that FileNotFoundError is raised for missing files."""
    with pytest.raises(FileNotFoundError):
        calculate_sha256("/nonexistent/path/file.txt")


def test_hash_directory():
    """Test hashing all files in a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some files
        file1 = Path(tmpdir) / "file1.txt"
        file2 = Path(tmpdir) / "file2.txt"
        file1.write_text("content1")
        file2.write_text("content2")

        hashes = hash_directory(tmpdir)

        assert len(hashes) == 2
        assert "file1.txt" in hashes
        assert "file2.txt" in hashes
        # Verify format is hex string
        assert all(len(h) == 64 for h in hashes.values())


def test_hash_directory_with_extensions():
    """Test hashing only specific file extensions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file1 = Path(tmpdir) / "file1.txt"
        file2 = Path(tmpdir) / "file2.csv"
        file3 = Path(tmpdir) / "file3.log"
        file1.write_text("txt")
        file2.write_text("csv")
        file3.write_text("log")

        # Only include .txt and .csv
        hashes = hash_directory(tmpdir, extensions=[".txt", ".csv"])

        assert len(hashes) == 2
        assert "file1.txt" in hashes
        assert "file2.csv" in hashes
        assert "file3.log" not in hashes


def test_create_manifest_and_verify():
    """Test creating a manifest and verifying it."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create files
        file1 = Path(tmpdir) / "data.txt"
        file1.write_text("test data")

        # Create manifest
        manifest_path = Path(tmpdir) / "manifest.json"
        hashes = create_manifest(tmpdir, manifest_path)

        assert manifest_path.exists()
        with open(manifest_path, "r") as f:
            loaded_manifest = json.load(f)
        assert "data.txt" in loaded_manifest

        # Verify
        assert verify_artifacts(manifest_path, tmpdir) is True

        # Corrupt a file and verify failure
        file1.write_text("corrupted data")
        assert verify_artifacts(manifest_path, tmpdir) is False
