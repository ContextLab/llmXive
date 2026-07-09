"""
Unit tests for checksum verification utilities.
"""

import json
import os
import tempfile
from pathlib import Path
import pytest

from utils.checksums import (
    compute_sha256,
    verify_checksum,
    save_checksums,
    load_checksums,
    generate_checksums_for_directory,
    verify_all_downloads,
)


class TestComputeSha256:
    def test_compute_sha256_known_file(self):
        """Test checksum computation on a known file content."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Hello, World!")
            temp_path = f.name

        try:
            checksum = compute_sha256(temp_path)
            # SHA-256 of "Hello, World!"
            expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
            assert checksum == expected
        finally:
            os.unlink(temp_path)

    def test_compute_sha256_empty_file(self):
        """Test checksum computation on an empty file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            temp_path = f.name

        try:
            checksum = compute_sha256(temp_path)
            # SHA-256 of empty string
            expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            assert checksum == expected
        finally:
            os.unlink(temp_path)

    def test_compute_sha256_nonexistent_file(self):
        """Test that FileNotFoundError is raised for non-existent file."""
        with pytest.raises(FileNotFoundError):
            compute_sha256("/nonexistent/path/file.txt")

    def test_compute_sha256_directory(self):
        """Test that ValueError is raised for directory path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError):
                compute_sha256(tmpdir)


class TestVerifyChecksum:
    def test_verify_checksum_match(self):
        """Test successful verification when checksums match."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Test data")
            temp_path = f.name

        try:
            checksum = compute_sha256(temp_path)
            is_valid, message = verify_checksum(temp_path, checksum)
            assert is_valid is True
            assert "verified" in message.lower()
        finally:
            os.unlink(temp_path)

    def test_verify_checksum_mismatch(self):
        """Test verification failure when checksums don't match."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Test data")
            temp_path = f.name

        try:
            is_valid, message = verify_checksum(temp_path, "wrong_checksum")
            assert is_valid is False
            assert "mismatch" in message.lower()
        finally:
            os.unlink(temp_path)

    def test_verify_checksum_nonexistent_file(self):
        """Test verification failure for non-existent file."""
        is_valid, message = verify_checksum("/nonexistent/file.txt", "some_checksum")
        assert is_valid is False
        assert "not found" in message.lower()


class TestSaveAndLoadChecksums:
    def test_save_and_load_checksums(self):
        """Test saving and loading checksums dictionary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checksum_file = Path(tmpdir) / "checksums.json"
            test_checksums = {
                "file1.txt": "abc123",
                "file2.csv": "def456",
            }

            save_checksums(test_checksums, str(checksum_file))
            loaded = load_checksums(str(checksum_file))

            assert loaded == test_checksums

    def test_load_checksums_nonexistent(self):
        """Test that FileNotFoundError is raised for non-existent checksum file."""
        with pytest.raises(FileNotFoundError):
            load_checksums("/nonexistent/checksums.json")

    def test_save_checksums_creates_directory(self):
        """Test that save_checksums creates parent directories if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = Path(tmpdir) / "nested" / "dir" / "checksums.json"
            test_checksums = {"file.txt": "abc123"}

            save_checksums(test_checksums, str(nested_path))
            assert nested_path.exists()


class TestGenerateChecksumsForDirectory:
    def test_generate_checksums_for_directory(self):
        """Test generating checksums for all files in a directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            file1 = Path(tmpdir) / "file1.txt"
            file2 = Path(tmpdir) / "file2.csv"
            file1.write_text("content1")
            file2.write_text("content2")

            checksums = generate_checksums_for_directory(tmpdir)

            assert len(checksums) == 2
            assert "file1.txt" in checksums
            assert "file2.csv" in checksums

            # Verify actual checksums
            assert checksums["file1.txt"] == compute_sha256(str(file1))
            assert checksums["file2.csv"] == compute_sha256(str(file2))

    def test_generate_checksums_nonexistent_directory(self):
        """Test that FileNotFoundError is raised for non-existent directory."""
        with pytest.raises(FileNotFoundError):
            generate_checksums_for_directory("/nonexistent/directory")

    def test_generate_checksums_not_a_directory(self):
        """Test that ValueError is raised when path is not a directory."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name

        try:
            with pytest.raises(ValueError):
                generate_checksums_for_directory(temp_path)
        finally:
            os.unlink(temp_path)


class TestVerifyAllDownloads:
    def test_verify_all_downloads_empty_directory(self):
        """Test verification when raw data directory is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create an empty directory
            results = verify_all_downloads(tmpdir)
            assert len(results) == 1
            assert results[0][1] is True  # is_valid should be True (no errors, just no files)

    def test_verify_all_downloads_no_checksums_file(self):
        """Test verification when no checksums file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a dummy file
            Path(tmpdir, "dummy.txt").write_text("test")
            results = verify_all_downloads(tmpdir)
            assert len(results) == 1
            assert results[0][1] is False  # Should fail because no checksums file
            assert "not found" in results[0][2].lower()

    def test_verify_all_downloads_with_checksums(self):
        """Test verification with existing checksums file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            file1 = Path(tmpdir) / "file1.txt"
            file2 = Path(tmpdir) / "file2.csv"
            file1.write_text("content1")
            file2.write_text("content2")

            # Create checksums file
            checksums = {
                "file1.txt": compute_sha256(str(file1)),
                "file2.csv": compute_sha256(str(file2)),
            }
            checksum_file = Path(tmpdir) / "checksums.json"
            with open(checksum_file, "w") as f:
                json.dump(checksums, f)

            results = verify_all_downloads(tmpdir)
            assert len(results) == 2
            # All should be valid
            assert all(r[1] is True for r in results)