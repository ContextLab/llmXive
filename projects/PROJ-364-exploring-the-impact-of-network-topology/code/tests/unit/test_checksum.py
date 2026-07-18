"""
Unit tests for checksum utilities.
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
    verify_manifest
)


class TestComputeStringSha256:
    def test_compute_string_sha256(self):
        """Test hashing a simple string."""
        data = "hello world"
        # Pre-calculated hash for "hello world"
        expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        assert compute_string_sha256(data) == expected

    def test_compute_string_sha256_empty(self):
        """Test hashing an empty string."""
        assert compute_string_sha256("") == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    def test_compute_string_sha256_type_error(self):
        """Test that non-string input raises TypeError."""
        with pytest.raises(TypeError):
            compute_string_sha256(12345)


class TestComputeFileSha256:
    def test_compute_file_sha256(self):
        """Test hashing a file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            # Pre-calculated hash for "test content"
            expected = "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"
            assert compute_file_sha256(temp_path) == expected
        finally:
            Path(temp_path).unlink()

    def test_compute_file_sha256_missing_file(self):
        """Test that missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            compute_file_sha256("/nonexistent/path/file.txt")

    def test_compute_file_sha256_directory(self):
        """Test that passing a directory raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError):
                compute_file_sha256(tmpdir)


class TestVerifyFileChecksum:
    def test_verify_file_checksum_success(self):
        """Test successful verification."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("verify me")
            temp_path = f.name

        try:
            # Hash for "verify me"
            expected_hash = "c8a6530682479753961827303533692398476743830550134795357747260154"
            assert verify_file_checksum(temp_path, expected_hash) is True
        finally:
            Path(temp_path).unlink()

    def test_verify_file_checksum_failure(self):
        """Test failed verification."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("wrong hash")
            temp_path = f.name

        try:
            wrong_hash = "0000000000000000000000000000000000000000000000000000000000000000"
            assert verify_file_checksum(temp_path, wrong_hash) is False
        finally:
            Path(temp_path).unlink()


class TestGenerateChecksumManifest:
    def test_generate_checksum_manifest(self):
        """Test manifest generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            file1 = tmpdir_path / "file1.txt"
            file2 = tmpdir_path / "file2.txt"
            
            file1.write_text("content 1")
            file2.write_text("content 2")

            # Change to tmpdir so relative paths work nicely
            import os
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                manifest = generate_checksum_manifest([str(file1), str(file2)])
                
                assert len(manifest) == 2
                assert "file1.txt" in manifest
                assert "file2.txt" in manifest
                assert len(manifest["file1.txt"]) == 64
                assert len(manifest["file2.txt"]) == 64
            finally:
                os.chdir(original_cwd)

    def test_generate_and_load_manifest(self):
        """Test generating and loading a manifest file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            file1 = tmpdir_path / "data.csv"
            file1.write_text("a,b\n1,2")
            
            manifest_path = tmpdir_path / "manifest.json"
            
            import os
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                generate_checksum_manifest([str(file1)], str(manifest_path))
                
                loaded = load_checksum_manifest(manifest_path)
                assert len(loaded) == 1
                assert "data.csv" in loaded
            finally:
                os.chdir(original_cwd)


class TestVerifyManifest:
    def test_verify_manifest(self):
        """Test verifying a manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            file1 = tmpdir_path / "valid.txt"
            file1.write_text("valid content")
            
            manifest_path = tmpdir_path / "manifest.json"
            
            import os
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                # Generate manifest
                generate_checksum_manifest([str(file1)], str(manifest_path))
                
                # Verify
                results = verify_manifest(manifest_path)
                assert results["valid.txt"] is True
                
                # Corrupt file
                file1.write_text("corrupted")
                results = verify_manifest(manifest_path)
                assert results["valid.txt"] is False
            finally:
                os.chdir(original_cwd)

    def test_verify_manifest_missing_file(self):
        """Test manifest verification with a missing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            manifest_path = tmpdir_path / "manifest.json"
            
            # Create a manifest pointing to a non-existent file
            fake_manifest = {
                "missing_file.txt": "0000000000000000000000000000000000000000000000000000000000000000"
            }
            manifest_path.write_text(json.dumps(fake_manifest))
            
            results = verify_manifest(manifest_path)
            assert results["missing_file.txt"] is False

    def test_load_manifest_missing_file(self):
        """Test loading a manifest that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_checksum_manifest("/nonexistent/manifest.json")