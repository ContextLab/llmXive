"""
Unit tests for manifest generation utility (T014).
Verifies SHA256 hash computation and manifest structure.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from code.src.utils.manifest import (
    compute_file_hash,
    scan_directory,
    generate_manifest,
    validate_manifest
)


class TestComputeFileHash:
    """Tests for compute_file_hash function."""

    def test_hash_sha256(self, tmp_path):
        """Test SHA256 hash computation for a simple file."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)

        hash_result = compute_file_hash(test_file)

        # Known SHA256 for "Hello, World!"
        expected = "315f5bdb76d078c43b8ac0064e4a0164612b1fce77c869345bfc94c75894edd3"
        assert hash_result == expected

    def test_hash_empty_file(self, tmp_path):
        """Test hash computation for an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")

        hash_result = compute_file_hash(test_file)

        # SHA256 for empty string
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert hash_result == expected

    def test_hash_large_file(self, tmp_path):
        """Test hash computation for a larger file (chunked reading)."""
        test_file = tmp_path / "large.bin"
        # Create a file larger than default chunk size (8KB)
        content = b"X" * (1024 * 1024)  # 1MB
        test_file.write_bytes(content)

        hash_result = compute_file_hash(test_file)

        # Verify it returns a valid hex string
        assert len(hash_result) == 64
        assert all(c in "0123456789abcdef" for c in hash_result)

    def test_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        non_existent = tmp_path / "nonexistent.txt"

        with pytest.raises(FileNotFoundError):
            compute_file_hash(non_existent)


class TestScanDirectory:
    """Tests for scan_directory function."""

    def test_scan_all_files(self, tmp_path):
        """Test scanning for all files."""
        (tmp_path / "file1.txt").write_text("a")
        (tmp_path / "file2.json").write_text("b")
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file3.txt").write_text("c")

        files = scan_directory(tmp_path)

        assert len(files) == 3
        assert all(f.exists() for f in files)

    def test_scan_with_extensions(self, tmp_path):
        """Test scanning with specific extensions."""
        (tmp_path / "file1.txt").write_text("a")
        (tmp_path / "file2.json").write_text("b")
        (tmp_path / "file3.py").write_text("c")

        files = scan_directory(tmp_path, extensions=[".json", ".txt"])

        assert len(files) == 2
        assert all(f.suffix in [".json", ".txt"] for f in files)

    def test_scan_with_exclusions(self, tmp_path):
        """Test scanning with exclusion patterns."""
        (tmp_path / "file1.txt").write_text("a")
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "cache.pyc").write_text("b")
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "config").write_text("c")

        files = scan_directory(tmp_path, exclude_patterns=["__pycache__", ".git"])

        assert len(files) == 1
        assert files[0].name == "file1.txt"

    def test_empty_directory(self, tmp_path):
        """Test scanning an empty directory."""
        files = scan_directory(tmp_path)
        assert files == []

    def test_nonexistent_directory(self, tmp_path):
        """Test scanning a nonexistent directory."""
        nonexistent = tmp_path / "does_not_exist"
        files = scan_directory(nonexistent)
        assert files == []


class TestGenerateManifest:
    """Tests for generate_manifest function."""

    def test_generate_basic_manifest(self, tmp_path):
        """Test basic manifest generation."""
        # Setup test files
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        (output_dir / "test1.json").write_text('{"a": 1}')
        (output_dir / "test2.csv").write_text("a,b\n1,2")

        manifest_path = tmp_path / "manifest.json"

        manifest = generate_manifest(
            target_dirs=[output_dir],
            output_path=manifest_path
        )

        # Verify manifest structure
        assert "version" in manifest
        assert "generated_at" in manifest
        assert "algorithm" in manifest
        assert manifest["algorithm"] == "sha256"
        assert "files" in manifest

        # Verify file entries
        assert len(manifest["files"]) == 2
        assert all(isinstance(h, str) and len(h) == 64 for h in manifest["files"].values())

        # Verify file was written
        assert manifest_path.exists()
        with open(manifest_path) as f:
            loaded = json.load(f)
        assert loaded == manifest

    def test_generate_with_multiple_dirs(self, tmp_path):
        """Test manifest generation from multiple directories."""
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()
        (dir1 / "file1.txt").write_text("a")
        (dir2 / "file2.txt").write_text("b")

        manifest_path = tmp_path / "manifest.json"

        manifest = generate_manifest(
            target_dirs=[dir1, dir2],
            output_path=manifest_path
        )

        assert len(manifest["files"]) == 2

    def test_generate_no_files(self, tmp_path):
        """Test that ValueError is raised when no files are found."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        manifest_path = tmp_path / "manifest.json"

        with pytest.raises(ValueError, match="No files found"):
            generate_manifest(
                target_dirs=[empty_dir],
                output_path=manifest_path
            )

    def test_generate_creates_output_dir(self, tmp_path):
        """Test that output directory is created if it doesn't exist."""
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("a")

        manifest_path = tmp_path / "nested" / "deep" / "manifest.json"

        generate_manifest(
            target_dirs=[test_dir],
            output_path=manifest_path
        )

        assert manifest_path.exists()


class TestValidateManifest:
    """Tests for validate_manifest function."""

    def test_validate_all_match(self, tmp_path):
        """Test validation when all hashes match."""
        # Create files and manifest
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        test_file = output_dir / "test.txt"
        test_file.write_text("content")

        manifest_path = tmp_path / "manifest.json"
        file_hash = compute_file_hash(test_file)

        manifest = {
            "version": "1.0",
            "generated_at": "2024-01-01T00:00:00Z",
            "algorithm": "sha256",
            "files": {
                "output/test.txt": file_hash
            }
        }

        with open(manifest_path, "w") as f:
            json.dump(manifest, f)

        is_valid = validate_manifest(manifest_path, tmp_path)
        assert is_valid is True

    def test_validate_hash_mismatch(self, tmp_path):
        """Test validation when hash does not match."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        test_file = output_dir / "test.txt"
        test_file.write_text("content")

        manifest_path = tmp_path / "manifest.json"
        wrong_hash = "0" * 64

        manifest = {
            "version": "1.0",
            "generated_at": "2024-01-01T00:00:00Z",
            "algorithm": "sha256",
            "files": {
                "output/test.txt": wrong_hash
            }
        }

        with open(manifest_path, "w") as f:
            json.dump(manifest, f)

        is_valid = validate_manifest(manifest_path, tmp_path)
        assert is_valid is False

    def test_validate_missing_file(self, tmp_path):
        """Test validation when file is missing."""
        manifest_path = tmp_path / "manifest.json"
        wrong_hash = "0" * 64

        manifest = {
            "version": "1.0",
            "generated_at": "2024-01-01T00:00:00Z",
            "algorithm": "sha256",
            "files": {
                "output/nonexistent.txt": wrong_hash
            }
        }

        with open(manifest_path, "w") as f:
            json.dump(manifest, f)

        is_valid = validate_manifest(manifest_path, tmp_path)
        assert is_valid is False

    def test_validate_manifest_not_found(self, tmp_path):
        """Test validation when manifest file is missing."""
        is_valid = validate_manifest(tmp_path / "nonexistent.json", tmp_path)
        assert is_valid is False