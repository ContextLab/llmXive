"""
Unit tests for the checksum verification infrastructure.
"""

import os
import tempfile
from pathlib import Path
import pytest

from src.utils.checksum import (
    compute_sha256,
    parse_manifest,
    verify_file,
    verify_manifest,
    create_manifest,
    DEFAULT_MANIFEST_PATH,
)


class TestComputeSha256:
    def test_compute_hash_known_value(self):
        """Test SHA-256 computation with a known string."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("test content")
            temp_path = f.name

        try:
            # SHA-256 of "test content"
            expected = "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"
            actual = compute_sha256(temp_path)
            assert actual == expected
        finally:
            os.unlink(temp_path)

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing files."""
        with pytest.raises(FileNotFoundError):
            compute_sha256("/nonexistent/path/file.txt")


class TestParseManifest:
    def test_parse_valid_manifest(self):
        """Test parsing a valid manifest file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("abc123  file1.txt\n")
            f.write("def456  file2.txt\n")
            f.write("# comment line\n")
            f.write("ghi789  file with spaces.txt\n")
            temp_path = f.name

        try:
            checksums = parse_manifest(temp_path)
            assert len(checksums) == 3
            assert checksums["file1.txt"] == "abc123"
            assert checksums["file2.txt"] == "def456"
            assert checksums["file with spaces.txt"] == "ghi789"
        finally:
            os.unlink(temp_path)

    def test_parse_invalid_line(self):
        """Test that ValueError is raised for invalid manifest lines."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("invalid_line_without_hash\n")
            temp_path = f.name

        try:
            with pytest.raises(ValueError):
                parse_manifest(temp_path)
        finally:
            os.unlink(temp_path)

    def test_manifest_not_found(self):
        """Test that FileNotFoundError is raised for missing manifest."""
        with pytest.raises(FileNotFoundError):
            parse_manifest("/nonexistent/manifest.txt")


class TestVerifyFile:
    def test_verify_correct_hash(self):
        """Test verification with correct hash."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("test content")
            temp_path = f.name

        try:
            expected = "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"
            assert verify_file(temp_path, expected) is True
        finally:
            os.unlink(temp_path)

    def test_verify_incorrect_hash(self):
        """Test verification with incorrect hash."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("test content")
            temp_path = f.name

        try:
            assert verify_file(temp_path, "wronghash") is False
        finally:
            os.unlink(temp_path)


class TestCreateManifest:
    def test_create_manifest_single_file(self):
        """Test creating a manifest for a directory with a single file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file
            test_file = os.path.join(tmpdir, "test.txt")
            with open(test_file, "w") as f:
                f.write("content")

            manifest_path = os.path.join(tmpdir, "checksums.txt")
            create_manifest(tmpdir, manifest_path)

            # Verify manifest was created
            assert os.path.exists(manifest_path)
            
            # Verify content
            with open(manifest_path, "r") as f:
                content = f.read()
                assert "test.txt" in content
                assert "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72" in content

    def test_create_manifest_recursive(self):
        """Test creating a recursive manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create subdirectory structure
            subdir = os.path.join(tmpdir, "subdir")
            os.makedirs(subdir)
            
            # Create files
            with open(os.path.join(tmpdir, "file1.txt"), "w") as f:
                f.write("content1")
            with open(os.path.join(subdir, "file2.txt"), "w") as f:
                f.write("content2")

            manifest_path = os.path.join(tmpdir, "checksums.txt")
            create_manifest(tmpdir, manifest_path, recursive=True)

            # Verify both files are in manifest
            with open(manifest_path, "r") as f:
                content = f.read()
                assert "file1.txt" in content
                assert "subdir/file2.txt" in content or "file2.txt" in content


class TestVerifyManifest:
    def test_verify_all_valid(self):
        """Test verifying a manifest where all files are valid."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            file1 = os.path.join(tmpdir, "file1.txt")
            file2 = os.path.join(tmpdir, "file2.txt")
            
            with open(file1, "w") as f:
                f.write("content1")
            with open(file2, "w") as f:
                f.write("content2")

            # Create manifest
            manifest_path = os.path.join(tmpdir, "checksums.txt")
            create_manifest(tmpdir, manifest_path)

            # Verify
            results = verify_manifest(manifest_path, tmpdir)
            
            assert len(results) == 2
            assert all(r[1] for r in results)  # All should be valid

    def test_verify_missing_file(self):
        """Test verifying a manifest with a missing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create only one file
            file1 = os.path.join(tmpdir, "file1.txt")
            with open(file1, "w") as f:
                f.write("content1")

            # Create manifest with both files (but file2 doesn't exist)
            manifest_path = os.path.join(tmpdir, "checksums.txt")
            with open(manifest_path, "w") as f:
                f.write(f"{compute_sha256(file1)}  file1.txt\n")
                f.write("abc123  file2.txt\n")

            # Verify
            results = verify_manifest(manifest_path, tmpdir)
            
            assert len(results) == 2
            assert results[0][1] is True  # file1 valid
            assert results[1][1] is False  # file2 missing

    def test_verify_hash_mismatch(self):
        """Test verifying a manifest with a hash mismatch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            file1 = os.path.join(tmpdir, "file1.txt")
            with open(file1, "w") as f:
                f.write("content1")

            # Create manifest with wrong hash
            manifest_path = os.path.join(tmpdir, "checksums.txt")
            with open(manifest_path, "w") as f:
                f.write("wronghash  file1.txt\n")

            # Verify
            results = verify_manifest(manifest_path, tmpdir)
            
            assert len(results) == 1
            assert results[0][1] is False  # Hash mismatch
            assert "Hash mismatch" in results[0][2]
