import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from reproduce import compute_file_checksum, verify_checksums, generate_checksum_manifest


class TestComputeFileChecksum:
    """Unit tests for compute_file_checksum function."""

    def test_compute_sha256_checksum(self):
        """Test that SHA-256 checksum is computed correctly."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test content for checksum")
            temp_path = f.name

        try:
            checksum = compute_file_checksum(temp_path)
            assert len(checksum) == 64  # SHA-256 hex length
            assert all(c in '0123456789abcdef' for c in checksum)
        finally:
            os.unlink(temp_path)

    def test_compute_checksum_nonexistent_file(self):
        """Test that FileNotFoundError is raised for non-existent file."""
        with pytest.raises(FileNotFoundError):
            compute_file_checksum("/nonexistent/path/file.txt")

    def test_compute_checksum_different_content(self):
        """Test that different content produces different checksums."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f1:
            f1.write("content A")
            path1 = f1.name

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f2:
            f2.write("content B")
            path2 = f2.name

        try:
            checksum1 = compute_file_checksum(path1)
            checksum2 = compute_file_checksum(path2)
            assert checksum1 != checksum2
        finally:
            os.unlink(path1)
            os.unlink(path2)

    def test_compute_checksum_same_content(self):
        """Test that same content produces same checksum."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f1:
            f1.write("identical content")
            path1 = f1.name

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f2:
            f2.write("identical content")
            path2 = f2.name

        try:
            checksum1 = compute_file_checksum(path1)
            checksum2 = compute_file_checksum(path2)
            assert checksum1 == checksum2
        finally:
            os.unlink(path1)
            os.unlink(path2)


class TestVerifyChecksums:
    """Unit tests for verify_checksums function."""

    def test_verify_all_match(self):
        """Test verification when all checksums match."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            file1 = os.path.join(tmpdir, "file1.txt")
            file2 = os.path.join(tmpdir, "file2.txt")

            with open(file1, 'w') as f:
                f.write("content 1")
            with open(file2, 'w') as f:
                f.write("content 2")

            # Compute actual checksums
            checksum1 = compute_file_checksum(file1)
            checksum2 = compute_file_checksum(file2)

            # Create expected checksums dict
            expected = {
                "file1.txt": checksum1,
                "file2.txt": checksum2
            }

            # Create manifest file
            manifest_path = os.path.join(tmpdir, "manifest.json")
            with open(manifest_path, 'w') as f:
                json.dump(expected, f)

            # Verify - need to adjust paths for the function
            with patch('reproduce.PROJECT_ROOT', Path(tmpdir)):
                all_match, mismatches = verify_checksums(manifest_path, expected)
                assert all_match is True
                assert len(mismatches) == 0

    def test_verify_checksum_mismatch(self):
        """Test verification when checksums don't match."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = os.path.join(tmpdir, "file1.txt")
            with open(file1, 'w') as f:
                f.write("content 1")

            actual_checksum = compute_file_checksum(file1)
            wrong_checksum = "a" * 64  # Invalid checksum

            expected = {"file1.txt": wrong_checksum}

            manifest_path = os.path.join(tmpdir, "manifest.json")
            with open(manifest_path, 'w') as f:
                json.dump(expected, f)

            with patch('reproduce.PROJECT_ROOT', Path(tmpdir)):
                all_match, mismatches = verify_checksums(manifest_path, expected)
                assert all_match is False
                assert len(mismatches) == 1
                assert "Checksum mismatch" in mismatches[0]

    def test_verify_missing_file(self):
        """Test verification when a file is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            expected = {"nonexistent.txt": "abc123"}

            manifest_path = os.path.join(tmpdir, "manifest.json")
            with open(manifest_path, 'w') as f:
                json.dump(expected, f)

            with patch('reproduce.PROJECT_ROOT', Path(tmpdir)):
                all_match, mismatches = verify_checksums(manifest_path, expected)
                assert all_match is False
                assert len(mismatches) == 1
                assert "File missing" in mismatches[0]

    def test_verify_missing_manifest(self):
        """Test verification when manifest file is missing."""
        expected = {"file.txt": "abc123"}
        all_match, mismatches = verify_checksums("/nonexistent/manifest.json", expected)
        assert all_match is False
        assert len(mismatches) == 1
        assert "Checksum file not found" in mismatches[0]


class TestGenerateChecksumManifest:
    """Unit tests for generate_checksum_manifest function."""

    def test_generate_manifest(self):
        """Test manifest generation for existing files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            file1 = os.path.join(tmpdir, "file1.txt")
            file2 = os.path.join(tmpdir, "file2.txt")

            with open(file1, 'w') as f:
                f.write("content 1")
            with open(file2, 'w') as f:
                f.write("content 2")

            # Relative paths
            rel_files = ["file1.txt", "file2.txt"]
            manifest_path = os.path.join(tmpdir, "manifest.json")

            with patch('reproduce.PROJECT_ROOT', Path(tmpdir)):
                checksums = generate_checksum_manifest(manifest_path, rel_files)

                assert len(checksums) == 2
                assert "file1.txt" in checksums
                assert "file2.txt" in checksums

                # Verify manifest file was created
                assert os.path.exists(manifest_path)

                # Verify content
                with open(manifest_path, 'r') as f:
                    loaded = json.load(f)
                assert loaded == checksums

    def test_generate_manifest_with_missing_file(self):
        """Test manifest generation when some files are missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = os.path.join(tmpdir, "file1.txt")
            with open(file1, 'w') as f:
                f.write("content 1")

            rel_files = ["file1.txt", "missing.txt"]
            manifest_path = os.path.join(tmpdir, "manifest.json")

            with patch('reproduce.PROJECT_ROOT', Path(tmpdir)):
                checksums = generate_checksum_manifest(manifest_path, rel_files)

                # Only existing file should be in checksums
                assert "file1.txt" in checksums
                assert "missing.txt" not in checksums
                assert len(checksums) == 1
