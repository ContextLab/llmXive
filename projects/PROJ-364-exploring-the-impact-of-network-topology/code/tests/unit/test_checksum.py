"""
Unit tests for the checksum module.
"""

import json
import tempfile
from pathlib import Path
import pytest

from src.utils.checksum import (
    compute_string_sha256,
    compute_file_sha256,
    verify_file_checksum,
    generate_checksum_manifest,
    load_checksum_manifest,
    verify_manifest,
    calculate_sha256
)


class TestComputeStringSha256:
    """Tests for compute_string_sha256 function."""

    def test_empty_string(self):
        """Test hashing an empty string."""
        result = compute_string_sha256("")
        # SHA-256 of empty string
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert result == expected

    def test_simple_string(self):
        """Test hashing a simple string."""
        result = compute_string_sha256("hello")
        expected = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
        assert result == expected

    def test_unicode_string(self):
        """Test hashing a string with unicode characters."""
        result = compute_string_sha256("héllo 世界")
        assert len(result) == 64  # SHA-256 hex is always 64 chars
        assert all(c in '0123456789abcdef' for c in result)

    def test_type_error_on_non_string(self):
        """Test that non-string input raises TypeError."""
        with pytest.raises(TypeError):
            compute_string_sha256(123)

        with pytest.raises(TypeError):
            compute_string_sha256(None)

        with pytest.raises(TypeError):
            compute_string_sha256(["hello"])


class TestComputeFileSha256:
    """Tests for compute_file_sha256 function."""

    def test_simple_file(self):
        """Test hashing a simple file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test content")
            temp_path = f.name

        try:
            result = compute_file_sha256(temp_path)
            assert len(result) == 64
            assert all(c in '0123456789abcdef' for c in result)
        finally:
            Path(temp_path).unlink()

    def test_binary_file(self):
        """Test hashing a binary file."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.bin') as f:
            f.write(b'\x00\x01\x02\x03\x04')
            temp_path = f.name

        try:
            result = compute_file_sha256(temp_path)
            assert len(result) == 64
        finally:
            Path(temp_path).unlink()

    def test_large_file(self):
        """Test hashing a larger file (tests chunking)."""
        content = "x" * (1024 * 1024)  # 1MB
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(content)
            temp_path = f.name

        try:
            result = compute_file_sha256(temp_path)
            assert len(result) == 64
        finally:
            Path(temp_path).unlink()

    def test_file_not_found(self):
        """Test that non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            compute_file_sha256("/nonexistent/path/file.txt")

    def test_path_object(self):
        """Test that Path objects are accepted."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test")
            temp_path = f.name

        try:
            result = compute_file_sha256(Path(temp_path))
            assert len(result) == 64
        finally:
            Path(temp_path).unlink()


class TestVerifyFileChecksum:
    """Tests for verify_file_checksum function."""

    def test_valid_checksum(self):
        """Test verification with correct checksum."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test content")
            temp_path = f.name

        try:
            actual_hash = compute_file_sha256(temp_path)
            result = verify_file_checksum(temp_path, actual_hash)
            assert result is True
        finally:
            Path(temp_path).unlink()

    def test_invalid_checksum(self):
        """Test verification with incorrect checksum."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test content")
            temp_path = f.name

        try:
            result = verify_file_checksum(temp_path, "wronghash123")
            assert result is False
        finally:
            Path(temp_path).unlink()

    def test_case_insensitive(self):
        """Test that checksum verification is case-insensitive."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test")
            temp_path = f.name

        try:
            actual_hash = compute_file_sha256(temp_path)
            upper_hash = actual_hash.upper()
            result = verify_file_checksum(temp_path, upper_hash)
            assert result is True
        finally:
            Path(temp_path).unlink()


class TestCalculateSha256:
    """Tests for the calculate_sha256 function (T008a requirement)."""

    def test_calculate_sha256_returns_correct_hash(self):
        """Test that calculate_sha256 returns the correct hash."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("hello world")
            temp_path = f.name

        try:
            result = calculate_sha256(temp_path)
            assert len(result) == 64
            assert all(c in '0123456789abcdef' for c in result)
        finally:
            Path(temp_path).unlink()

    def test_calculate_sha256_file_not_found(self):
        """Test that calculate_sha256 raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            calculate_sha256("/nonexistent/file.txt")


class TestGenerateChecksumManifest:
    """Tests for generate_checksum_manifest function."""

    def test_generate_manifest(self):
        """Test generating a manifest with multiple files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            file1 = Path(tmpdir) / "file1.txt"
            file2 = Path(tmpdir) / "file2.txt"
            file1.write_text("content 1")
            file2.write_text("content 2")

            manifest_path = Path(tmpdir) / "manifest.json"

            result_path = generate_checksum_manifest([str(file1), str(file2)], manifest_path)

            assert result_path.exists()

            # Load and verify manifest
            with open(result_path) as f:
                manifest = json.load(f)

            assert manifest["version"] == "1.0"
            assert manifest["algorithm"] == "sha256"
            assert str(file1) in manifest["files"]
            assert str(file2) in manifest["files"]
            assert "hash" in manifest["files"][str(file1)]
            assert "size_bytes" in manifest["files"][str(file1)]

    def test_creates_parent_directory(self):
        """Test that manifest generation creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.txt"
            file_path.write_text("test")

            manifest_path = Path(tmpdir) / "nested" / "dir" / "manifest.json"

            generate_checksum_manifest([str(file_path)], manifest_path)
            assert manifest_path.exists()


class TestLoadChecksumManifest:
    """Tests for load_checksum_manifest function."""

    def test_load_valid_manifest(self):
        """Test loading a valid manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
          manifest_path = Path(tmpdir) / "manifest.json"
          manifest_data = {
              "version": "1.0",
              "algorithm": "sha256",
              "files": {
                  "/test/file.txt": {"hash": "abc123", "size_bytes": 100}
              }
          }

          with open(manifest_path, 'w') as f:
              json.dump(manifest_data, f)

          result = load_checksum_manifest(manifest_path)
          assert result["version"] == "1.0"
          assert result["algorithm"] == "sha256"

    def test_load_nonexistent_manifest(self):
        """Test that loading a non-existent manifest raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_checksum_manifest("/nonexistent/manifest.json")


class TestVerifyManifest:
    """Tests for verify_manifest function."""

    def test_verify_all_valid(self):
        """Test verifying a manifest where all files are valid."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            file_path = Path(tmpdir) / "test.txt"
            file_path.write_text("test content")
            file_hash = compute_file_sha256(file_path)

            # Create manifest
            manifest_path = Path(tmpdir) / "manifest.json"
            manifest_data = {
                "version": "1.0",
                "algorithm": "sha256",
                "files": {
                    str(file_path): {"hash": file_hash, "size_bytes": file_path.stat().st_size}
                }
            }

            with open(manifest_path, 'w') as f:
                json.dump(manifest_data, f)

            results = verify_manifest(manifest_path)
            assert results[str(file_path)] is True

    def test_verify_mixed_results(self):
        """Test verifying a manifest with some valid and some invalid files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create valid file
            file1 = Path(tmpdir) / "valid.txt"
            file1.write_text("valid content")
            file1_hash = compute_file_sha256(file1)

            # Create invalid file (content changed after hash)
            file2 = Path(tmpdir) / "invalid.txt"
            file2.write_text("original content")
            file2_hash = compute_file_sha256(file2)
            file2.write_text("modified content")  # Change content

            manifest_path = Path(tmpdir) / "manifest.json"
            manifest_data = {
                "version": "1.0",
                "algorithm": "sha256",
                "files": {
                    str(file1): {"hash": file1_hash, "size_bytes": file1.stat().st_size},
                    str(file2): {"hash": file2_hash, "size_bytes": file2.stat().st_size}
                }
            }

            with open(manifest_path, 'w') as f:
                json.dump(manifest_data, f)

            results = verify_manifest(manifest_path)
            assert results[str(file1)] is True
            assert results[str(file2)] is False