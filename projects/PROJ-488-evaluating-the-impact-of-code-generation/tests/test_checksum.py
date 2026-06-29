"""
Tests for the checksum utilities module.

These tests verify that SHA-256 checksum computation, storage, and
verification work correctly.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest import TestCase
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.checksum import (
    compute_sha256,
    compute_directory_checksums,
    write_checksums,
    read_checksums,
    verify_checksums,
    register_dataset_checksum,
)


class TestComputeSha256(TestCase):
    """Tests for compute_sha256 function."""

    def test_compute_sha256_known_value(self):
        """Test that we compute correct SHA-256 for known content."""
        # Test with empty file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("")
            temp_path = f.name

        try:
            checksum = compute_sha256(temp_path)
            # SHA-256 of empty string
            expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            self.assertEqual(checksum, expected)
        finally:
            os.unlink(temp_path)

    def test_compute_sha256_with_content(self):
        """Test SHA-256 computation for file with known content."""
        content = "Hello, World!"
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write(content)
            temp_path = f.name

        try:
            checksum = compute_sha256(temp_path)
            # SHA-256 of "Hello, World!"
            expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
            self.assertEqual(checksum, expected)
        finally:
            os.unlink(temp_path)

    def test_compute_sha256_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with self.assertRaises(FileNotFoundError):
            compute_sha256("/nonexistent/path/to/file.txt")

    def test_compute_sha256_directory_error(self):
        """Test that IsADirectoryError is raised for directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(IsADirectoryError):
                compute_sha256(tmpdir)


class TestComputeDirectoryChecksums(TestCase):
    """Tests for compute_directory_checksums function."""

    def test_compute_directory_checksums_single_file(self):
        """Test checksum computation for directory with single file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test content")

            checksums = compute_directory_checksums(tmpdir)

            self.assertIn("test.txt", checksums)
            self.assertEqual(len(checksums), 1)

    def test_compute_directory_checksums_recursive(self):
        """Test recursive checksum computation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested directory structure
            subdir = Path(tmpdir) / "subdir"
            subdir.mkdir()

            file1 = Path(tmpdir) / "file1.txt"
            file1.write_text("content1")

            file2 = subdir / "file2.txt"
            file2.write_text("content2")

            checksums = compute_directory_checksums(tmpdir, recursive=True)

            self.assertIn("file1.txt", checksums)
            self.assertIn("subdir/file2.txt", checksums)
            self.assertEqual(len(checksums), 2)

    def test_compute_directory_checksums_with_extension_filter(self):
        """Test checksum computation with extension filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / "test.json"
            file1.write_text("{}")

            file2 = Path(tmpdir) / "test.txt"
            file2.write_text("text")

            checksums = compute_directory_checksums(tmpdir, extensions=[".json"])

            self.assertIn("test.json", checksums)
            self.assertNotIn("test.txt", checksums)
            self.assertEqual(len(checksums), 1)

    def test_compute_directory_checksums_not_found(self):
        """Test that FileNotFoundError is raised for missing directory."""
        with self.assertRaises(FileNotFoundError):
            compute_directory_checksums("/nonexistent/directory")


class TestWriteAndReadChecksums(TestCase):
    """Tests for write_checksums and read_checksums functions."""

    def test_write_and_read_checksums(self):
        """Test writing and reading checksums from JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "checksums.json"
            checksums = {
                "file1.txt": "abc123",
                "file2.txt": "def456",
            }

            write_checksums(checksums, output_path)

            read = read_checksums(output_path)
            self.assertEqual(read, checksums)

    def test_write_checksums_creates_parent_dirs(self):
        """Test that write_checksums creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "nested" / "dir" / "checksums.json"
            checksums = {"test.txt": "abc123"}

            write_checksums(checksums, output_path)

            self.assertTrue(output_path.exists())

    def test_read_checksums_file_not_found(self):
        """Test that FileNotFoundError is raised for missing checksums file."""
        with self.assertRaises(FileNotFoundError):
            read_checksums("/nonexistent/checksums.json")


class TestVerifyChecksums(TestCase):
    """Tests for verify_checksums function."""

    def test_verify_checksums_all_valid(self):
        """Test verification when all files match stored checksums."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create test file
            test_file = tmpdir / "test.txt"
            test_file.write_text("test content")

            # Create checksums file
            checksums_file = tmpdir / "checksums.json"
            checksums = {"test.txt": compute_sha256(test_file)}
            write_checksums(checksums, checksums_file)

            results = verify_checksums(tmpdir, checksums_file)

            self.assertIn("test.txt", results)
            self.assertTrue(results["test.txt"])

    def test_verify_checksums_invalid(self):
        """Test verification when file checksum doesn't match."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create test file
            test_file = tmpdir / "test.txt"
            test_file.write_text("test content")

            # Create checksums file with wrong checksum
            checksums_file = tmpdir / "checksums.json"
            checksums = {"test.txt": "wrongchecksum"}
            write_checksums(checksums, checksums_file)

            results = verify_checksums(tmpdir, checksums_file)

            self.assertIn("test.txt", results)
            self.assertFalse(results["test.txt"])

    def test_verify_checksums_missing_file(self):
        """Test verification when file is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create checksums file for non-existent file
            checksums_file = tmpdir / "checksums.json"
            checksums = {"missing.txt": "somechecksum"}
            write_checksums(checksums, checksums_file)

            results = verify_checksums(tmpdir, checksums_file)

            self.assertIn("missing.txt", results)
            self.assertFalse(results["missing.txt"])

    def test_verify_checksums_not_strict(self):
        """Test verification with strict=False when file missing."""
        results = verify_checksums("/tmp", "/nonexistent/checksums.json", strict=False)
        self.assertEqual(results, {})


class TestRegisterDatasetChecksum(TestCase):
    """Tests for register_dataset_checksum function."""

    def test_register_dataset_checksum_creates_file(self):
        """Test that register_dataset_checksum creates checksums file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            data_dir = tmpdir / "data"
            data_dir.mkdir()

            # Create test file
            test_file = data_dir / "dataset.json"
            test_file.write_text('{"data": "test"}')

            output_path = register_dataset_checksum(
                "test_dataset",
                test_file,
                data_dir / "checksums.json"
            )

            self.assertTrue(output_path.exists())

            # Verify checksum was recorded
            checksums = read_checksums(output_path)
            self.assertIn(str(test_file), checksums)

    def test_register_dataset_checksum_updates_existing(self):
        """Test that register_dataset_checksum updates existing checksums."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            data_dir = tmpdir / "data"
            data_dir.mkdir()

            # Create first file and register
            file1 = data_dir / "file1.txt"
            file1.write_text("content1")
            output_path = register_dataset_checksum(
                "dataset1",
                file1,
                data_dir / "checksums.json"
            )

            # Create second file and register
            file2 = data_dir / "file2.txt"
            file2.write_text("content2")
            output_path = register_dataset_checksum(
                "dataset2",
                file2,
                data_dir / "checksums.json"
            )

            # Both should be in checksums
            checksums = read_checksums(output_path)
            self.assertIn(str(file1), checksums)
            self.assertIn(str(file2), checksums)
            self.assertEqual(len(checksums), 2)


@pytest.mark.integration
class TestChecksumIntegration(TestCase):
    """Integration tests that verify end-to-end checksum workflow."""

    def test_full_checksum_workflow(self):
        """Test complete workflow: compute, write, verify."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create directory structure
            data_dir = tmpdir / "data" / "raw"
            data_dir.mkdir(parents=True)

            # Create test dataset files
            dataset1 = data_dir / "code_search_net.json"
            dataset1.write_text('{"snippets": [{"code": "def test(): pass"}]}')

            dataset2 = data_dir / "codegen.json"
            dataset2.write_text('{"snippets": [{"code": "def codegen(): pass"}]}')

            # Compute and write checksums
            checksums = {}
            for f in [dataset1, dataset2]:
                checksums[str(f)] = compute_sha256(f)

            output_path = write_checksums(
                checksums,
                data_dir / "checksums.json",
                description="Dataset checksums for CodeSearchNet and CodeGen"
            )

            # Verify checksums
            results = verify_checksums(data_dir.parent.parent, output_path)

            # All should pass
            for file_path, is_valid in results.items():
                self.assertTrue(is_valid, f"Checksum failed for {file_path}")

            # Verify JSON structure
            with open(output_path, "r") as f:
                data = json.load(f)

            self.assertIn("checksums", data)
            self.assertIn("algorithm", data)
            self.assertEqual(data["algorithm"], "sha256")
            self.assertIn("description", data)
