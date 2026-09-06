import os
import sys
import json
import hashlib
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd
import numpy as np

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from reproduce import compute_file_checksum, verify_checksums, generate_checksum_manifest

class TestComputeFileChecksum:
    def test_compute_sha256_checksum(self, tmp_path):
        """Test that compute_file_checksum returns correct SHA-256 hash."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        checksum = compute_file_checksum(test_file)
        expected = hashlib.sha256(content).hexdigest()
        
        assert checksum == expected
        assert len(checksum) == 64  # SHA-256 hex length

    def test_compute_checksum_nonexistent_file(self, tmp_path):
        """Test that compute_file_checksum raises FileNotFoundError."""
        nonexistent = tmp_path / "does_not_exist.txt"
        
        with pytest.raises(FileNotFoundError):
            compute_file_checksum(nonexistent)

class TestVerifyChecksums:
    def test_verify_checksums_all_valid(self, tmp_path):
        """Test verification when all checksums match."""
        # Create test file
        test_file = tmp_path / "data.csv"
        test_file.write_text("a,b\n1,2\n3,4")
        
        # Create manifest
        actual_checksum = compute_file_checksum(test_file)
        expected_checksums = {"data.csv": actual_checksum}
        
        # Create manifest file
        manifest_file = tmp_path / "manifest.json"
        with open(manifest_file, "w") as f:
            json.dump({"file": "data.csv", "checksum": actual_checksum}, f)
        
        # Change to temp dir to simulate relative paths
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            success, errors = verify_checksums(manifest_file, expected_checksums)
            assert success is True
            assert len(errors) == 0
        finally:
            os.chdir(original_cwd)

    def test_verify_checksums_mismatch(self, tmp_path):
        """Test verification when checksums don't match."""
        test_file = tmp_path / "data.csv"
        test_file.write_text("a,b\n1,2\n3,4")
        
        # Create manifest with wrong checksum
        wrong_checksum = "a" * 64
        expected_checksums = {"data.csv": wrong_checksum}
        
        manifest_file = tmp_path / "manifest.json"
        with open(manifest_file, "w") as f:
            json.dump({"file": "data.csv", "checksum": wrong_checksum}, f)
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            success, errors = verify_checksums(manifest_file, expected_checksums)
            assert success is False
            assert len(errors) == 1
            assert "Checksum mismatch" in errors[0]
        finally:
            os.chdir(original_cwd)

    def test_verify_checksums_missing_file(self, tmp_path):
        """Test verification when file is missing."""
        expected_checksums = {"missing.csv": "a" * 64}
        
        manifest_file = tmp_path / "manifest.json"
        with open(manifest_file, "w") as f:
            json.dump({"file": "missing.csv", "checksum": "a" * 64}, f)
        
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            success, errors = verify_checksums(manifest_file, expected_checksums)
            assert success is False
            assert len(errors) == 1
            assert "Missing file" in errors[0]
        finally:
            os.chdir(original_cwd)

class TestGenerateChecksumManifest:
    def test_generate_manifest(self, tmp_path):
        """Test manifest generation for multiple files."""
        # Create test files
        file1 = tmp_path / "file1.csv"
        file1.write_text("1,2")
        
        file2 = tmp_path / "file2.csv"
        file2.write_text("3,4")
        
        files = ["file1.csv", "file2.csv"]
        manifest = generate_checksum_manifest(tmp_path, files)
        
        assert len(manifest) == 2
        assert "file1.csv" in manifest
        assert "file2.csv" in manifest
        
        # Verify checksums are correct
        expected1 = compute_file_checksum(file1)
        expected2 = compute_file_checksum(file2)
        
        assert manifest["file1.csv"] == expected1
        assert manifest["file2.csv"] == expected2

    def test_generate_manifest_skips_missing(self, tmp_path):
        """Test that missing files are skipped in manifest generation."""
        file1 = tmp_path / "file1.csv"
        file1.write_text("1,2")
        
        files = ["file1.csv", "missing.csv"]
        manifest = generate_checksum_manifest(tmp_path, files)
        
        assert len(manifest) == 1
        assert "file1.csv" in manifest
        assert "missing.csv" not in manifest
