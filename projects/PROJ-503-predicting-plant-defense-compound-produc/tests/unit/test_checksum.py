"""
Unit tests for the SHA-256 checksum validation utility (T022).
"""

import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the utility functions
from code.utils.checksum import (
    calculate_sha256,
    load_checksums,
    save_checksums,
    validate_checksum,
    validate_checksums_from_manifest,
    generate_checksums
)
from code.exceptions import E_DATASET


class TestCalculateSHA256:
    def test_calculate_hash(self):
        """Test that calculate_sha256 returns a valid hex string."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test data")
            tmp_path = tmp.name

        try:
            hash_val = calculate_sha256(tmp_path)
            assert len(hash_val) == 64  # SHA-256 hex length
            assert all(c in '0123456789abcdef' for c in hash_val)
        finally:
            os.unlink(tmp_path)

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing files."""
        with pytest.raises(FileNotFoundError):
            calculate_sha256("/nonexistent/path/file.txt")

    def test_known_hash(self):
        """Test against a known input/output pair."""
        # "hello" -> 2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as tmp:
            tmp.write("hello")
            tmp_path = tmp.name

        try:
            hash_val = calculate_sha256(tmp_path)
            expected = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
            assert hash_val == expected
        finally:
            os.unlink(tmp_path)


class TestValidateChecksum:
    def test_valid_checksum(self):
        """Test that validate_checksum returns True for matching hash."""
        content = b"valid content for testing"
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Calculate the real hash first
            real_hash = calculate_sha256(tmp_path)
            
            # Validate it
            result = validate_checksum(tmp_path, real_hash)
            assert result is True
        finally:
            os.unlink(tmp_path)

    def test_invalid_checksum(self):
        """Test that ValueError is raised for mismatched hash."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"some content")
            tmp_path = tmp.name

        try:
            with pytest.raises(ValueError, match="Checksum mismatch"):
                validate_checksum(tmp_path, "0000000000000000000000000000000000000000000000000000000000000000")
        finally:
            os.unlink(tmp_path)

    def test_case_insensitivity(self):
        """Test that hash comparison is case-insensitive."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test")
            tmp_path = tmp.name

        try:
            real_hash = calculate_sha256(tmp_path)
            upper_hash = real_hash.upper()
            
            # Should pass despite case difference
            result = validate_checksum(tmp_path, upper_hash)
            assert result is True
        finally:
            os.unlink(tmp_path)


class TestLoadSaveChecksums:
    def test_save_and_load(self):
        """Test saving and loading a checksum manifest."""
        test_data = {
            "file1.txt": "hash1",
            "file2.csv": "hash2"
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = os.path.join(tmpdir, "checksums.json")
            
            # Save
            save_checksums(test_data, manifest_path)
            assert os.path.exists(manifest_path)

            # Load
            loaded = load_checksums(manifest_path)
            assert loaded == test_data

    def test_load_missing_file(self):
        """Test that FileNotFoundError is raised when manifest is missing."""
        with pytest.raises(FileNotFoundError):
            load_checksums("/nonexistent/manifest.json")


class TestValidateFromManifest:
    def test_validate_batch(self):
        """Test validating multiple files from a manifest."""
        files = []
        checksums = {}
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            for i in range(3):
                fname = f"test_{i}.txt"
                fpath = os.path.join(tmpdir, fname)
                content = f"content {i}".encode()
                
                with open(fpath, "wb") as f:
                    f.write(content)
                
                files.append(fpath)
                checksums[fname] = calculate_sha256(fpath)

            # Create manifest
            manifest_path = os.path.join(tmpdir, "manifest.json")
            save_checksums(checksums, manifest_path)

            # Validate
            results = validate_checksums_from_manifest(manifest_path, tmpdir)
            
            assert len(results) == 3
            assert all(results.values())  # All should be True

    def test_validate_with_mismatch(self):
        """Test that validation fails correctly for a bad hash in manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file
            fname = "bad_file.txt"
            fpath = os.path.join(tmpdir, fname)
            with open(fpath, "wb") as f:
                f.write(b"real content")
            
            # Create manifest with WRONG hash
            bad_hash = "0" * 64
            manifest_data = {fname: bad_hash}
            manifest_path = os.path.join(tmpdir, "manifest.json")
            save_checksums(manifest_data, manifest_path)

            # Validate
            results = validate_checksums_from_manifest(manifest_path, tmpdir)
            
            assert results[fname] is False
