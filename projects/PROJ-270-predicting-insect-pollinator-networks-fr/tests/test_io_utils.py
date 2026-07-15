"""
Tests for code/utils/io_utils.py
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the module under test
# We assume the test runner adds the project root to sys.path
# or we import relative to the code structure.
# Since T001b created __init__.py in code/, we can try importing from code.utils
import sys
from pathlib import Path

# Ensure we can import from the code directory
project_root = Path(__file__).resolve().parent.parent
code_dir = project_root / 'code'
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils.io_utils import (
    ensure_directory_structure,
    compute_file_checksum,
    verify_checksum,
    load_checksum_manifest,
    validate_data_integrity,
    get_file_size_mb
)


class TestEnsureDirectoryStructure:
    def test_creates_required_dirs(self, tmp_path):
        """Verify that all required directories are created."""
        dirs = ensure_directory_structure(base_path=tmp_path)
        
        assert 'root' in dirs
        assert 'data' in dirs
        assert 'raw' in dirs
        assert 'processed' in dirs
        assert 'figures' in dirs
        assert 'results' in dirs
        
        # Verify they actually exist on disk
        for key, path in dirs.items():
            assert path.exists(), f"Directory {key} ({path}) was not created."
        
        # Verify hierarchy
        assert dirs['raw'].parent == dirs['data']
        assert dirs['processed'].parent == dirs['data']

    def test_idempotent(self, tmp_path):
        """Verify that calling the function twice doesn't raise errors."""
        ensure_directory_structure(base_path=tmp_path)
        # Second call should not raise
        dirs = ensure_directory_structure(base_path=tmp_path)
        assert dirs['raw'].exists()


class TestChecksumUtilities:
    def test_compute_sha256(self, tmp_path):
        """Test checksum computation on a known file."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)

        checksum = compute_file_checksum(test_file, 'sha256')
        
        # Expected SHA256 for "Hello, World!"
        expected = "7f83b1657ff1fc53b92dc18148a1d65dfa66d704b47201b02d546e0651e3e37d"
        assert checksum == expected

    def test_compute_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for missing files."""
        missing_file = tmp_path / "nonexistent.txt"
        with pytest.raises(FileNotFoundError):
            compute_file_checksum(missing_file)

    def test_verify_checksum_match(self, tmp_path):
        """Test verification when checksum matches."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Test content")
        checksum = compute_file_checksum(test_file)
        
        assert verify_checksum(test_file, checksum) is True

    def test_verify_checksum_mismatch(self, tmp_path):
        """Test verification when checksum does not match."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Test content")
        
        # Wrong checksum
        assert verify_checksum(test_file, "wrong_checksum") is False

    def test_verify_missing_file(self, tmp_path):
        """Test verification returns False for missing files (no exception)."""
        missing_file = tmp_path / "nonexistent.txt"
        assert verify_checksum(missing_file, "some_hash") is False


class TestManifestUtilities:
    def test_load_manifest(self, tmp_path):
        """Test loading a valid JSON manifest."""
        manifest_data = {
            "raw/data.csv": "abc123",
            "processed/model.pkl": "def456"
        }
        manifest_file = tmp_path / "manifest.json"
        with open(manifest_file, 'w') as f:
            json.dump(manifest_data, f)

        loaded = load_checksum_manifest(manifest_file, base_path=tmp_path)
        assert loaded == manifest_data

    def test_load_missing_manifest(self, tmp_path):
        """Test loading a non-existent manifest returns empty dict."""
        result = load_checksum_manifest(tmp_path / "missing.json", base_path=tmp_path)
        assert result == {}

    def test_validate_data_integrity_valid(self, tmp_path):
        """Test validation when files match checksums."""
        # Setup directory structure
        data_dir = tmp_path / "data"
        raw_dir = data_dir / "raw"
        raw_dir.mkdir(parents=True)

        # Create a file
        test_file = raw_dir / "sample.txt"
        test_file.write_bytes(b"Sample data")
        real_hash = compute_file_checksum(test_file)

        # Create manifest
        manifest_file = tmp_path / "manifest.json"
        with open(manifest_file, 'w') as f:
            json.dump({"raw/sample.txt": real_hash}, f)

        results = validate_data_integrity(
            manifest_path=manifest_file,
            data_root=data_dir,
            base_path=tmp_path
        )

        assert results["raw/sample.txt"] == "valid"

    def test_validate_data_integrity_missing(self, tmp_path):
        """Test validation when file is missing."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        manifest_file = tmp_path / "manifest.json"
        with open(manifest_file, 'w') as f:
            json.dump({"raw/missing.txt": "somehash"}, f)

        results = validate_data_integrity(
            manifest_path=manifest_file,
            data_root=data_dir,
            base_path=tmp_path
        )

        assert results["raw/missing.txt"] == "missing"

    def test_validate_data_integrity_mismatch(self, tmp_path):
        """Test validation when checksum mismatches."""
        data_dir = tmp_path / "data"
        raw_dir = data_dir / "raw"
        raw_dir.mkdir(parents=True)

        test_file = raw_dir / "sample.txt"
        test_file.write_bytes(b"Data")
        
        manifest_file = tmp_path / "manifest.json"
        with open(manifest_file, 'w') as f:
            json.dump({"raw/sample.txt": "wrong_hash"}, f)

        results = validate_data_integrity(
            manifest_path=manifest_file,
            data_root=data_dir,
            base_path=tmp_path
        )

        assert results["raw/sample.txt"] == "mismatch"


class TestFileSize:
    def test_get_file_size(self, tmp_path):
        """Test getting file size in MB."""
        test_file = tmp_path / "test.txt"
        content = b"0" * 1024  # 1 KB
        test_file.write_bytes(content)

        size_mb = get_file_size_mb(test_file)
        # 1 KB = 0.0009765625 MB
        assert abs(size_mb - 0.0009765625) < 1e-6

    def test_get_file_size_missing(self, tmp_path):
        """Test getting size of missing file returns 0."""
        size_mb = get_file_size_mb(tmp_path / "nonexistent.txt")
        assert size_mb == 0.0