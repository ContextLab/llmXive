"""
Unit tests for code/utils/checksums.py (T007).
"""
import json
import tempfile
from pathlib import Path

import pytest

from code.utils.checksums import (
    compute_sha256,
    compute_directory_checksums,
    load_state_file,
    update_state_file,
    verify_file_integrity,
    verify_manifest,
    write_manifest,
)


class TestComputeSha256:
    """Test SHA-256 computation."""

    def test_compute_sha256_simple(self, tmp_path):
        """Test that compute_sha256 returns correct hash for a simple file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")
        
        # Known SHA-256 of "hello world"
        expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        result = compute_sha256(test_file)
        assert result == expected

    def test_compute_sha256_nonexistent(self):
        """Test that compute_sha256 raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            compute_sha256(Path("/nonexistent/file.txt"))

    def test_compute_sha256_binary(self, tmp_path):
        """Test SHA-256 on binary data."""
        test_file = tmp_path / "test.bin"
        test_file.write_bytes(b"\x00\x01\x02\x03")
        
        # Compute and verify it's a valid hex string
        result = compute_sha256(test_file)
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)


class TestDirectoryChecksums:
    """Test directory checksum computation."""

    def test_compute_directory_checksums_flat(self, tmp_path):
        """Test checksums for a flat directory."""
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")
        
        checksums = compute_directory_checksums(tmp_path, recursive=False)
        
        assert len(checksums) == 2
        assert "file1.txt" in checksums
        assert "file2.txt" in checksums
        assert checksums["file1.txt"] != checksums["file2.txt"]

    def test_compute_directory_checksums_recursive(self, tmp_path):
        """Test checksums for nested directories."""
        (tmp_path / "subdir").mkdir()
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "subdir" / "file2.txt").write_text("content2")
        
        checksums = compute_directory_checksums(tmp_path, recursive=True)
        
        assert len(checksums) == 2
        assert "file1.txt" in checksums
        assert str(Path("subdir") / "file2.txt") in checksums

    def test_compute_directory_checksums_excludes_pycache(self, tmp_path):
        """Test that __pycache__ is excluded."""
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "module.pyc").write_bytes(b"fake")
        (tmp_path / "file.txt").write_text("content")
        
        checksums = compute_directory_checksums(tmp_path, recursive=True)
        
        assert len(checksums) == 1
        assert "file.txt" in checksums


class TestStateFile:
    """Test state file loading and updating."""

    def test_load_state_file_missing(self, tmp_path):
        """Test that loading a missing state file returns empty dict."""
        result = load_state_file(tmp_path / "missing.json")
        assert result == {}

    def test_load_state_file_valid(self, tmp_path):
        """Test loading a valid state file."""
        state_file = tmp_path / "state.json"
        state_file.write_text('{"key": "value"}')
        
        result = load_state_file(state_file)
        assert result == {"key": "value"}

    def test_load_state_file_corrupt(self, tmp_path):
        """Test that corrupt JSON raises ValueError."""
        state_file = tmp_path / "corrupt.json"
        state_file.write_text("{invalid json}")
        
        with pytest.raises(ValueError, match="Corrupt state file"):
            load_state_file(state_file)

    def test_update_state_file_merge(self):
        """Test that update_state_file merges checksums correctly."""
        current_state = {"existing_file.txt": "hash1"}
        new_checksums = {
            "data/raw": {"file1.txt": "hash2", "file2.txt": "hash3"}
        }
        
        result = update_state_file(current_state, new_checksums, save=False)
        
        # Verify flat structure (no double-nesting)
        assert "existing_file.txt" in result
        assert "data/raw/file1.txt" in result
        assert "data/raw/file2.txt" in result
        assert result["data/raw/file1.txt"] == "hash2"
        assert result["data/raw/file2.txt"] == "hash3"
        # Ensure no double-nested 'checksums' key
        assert "checksums" not in str(result)

    def test_update_state_file_save(self, tmp_path):
        """Test that update_state_file saves to disk when save=True."""
        state_file = tmp_path / "state.json"
        current_state = {}
        new_checksums = {"data/raw": {"file.txt": "hash123"}}
        
        result = update_state_file(
            current_state, new_checksums, save=True, state_path=state_file
        )
        
        assert state_file.exists()
        saved_state = json.loads(state_file.read_text())
        assert "data/raw/file.txt" in saved_state
        assert saved_state["data/raw/file.txt"] == "hash123"

    def test_update_state_file_save_requires_path(self):
        """Test that save=True without state_path raises ValueError."""
        with pytest.raises(ValueError, match="state_path required"):
            update_state_file({}, {}, save=True, state_path=None)


class TestVerification:
    """Test integrity verification functions."""

    def test_verify_file_integrity_match(self, tmp_path):
        """Test verify_file_integrity when hash matches."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello")
        
        expected_hash = compute_sha256(test_file)
        result = verify_file_integrity(test_file, expected_hash)
        
        assert result is True

    def test_verify_file_integrity_mismatch(self, tmp_path):
        """Test verify_file_integrity when hash does not match."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello")
        
        result = verify_file_integrity(test_file, "wronghash")
        
        assert result is False

    def test_verify_file_integrity_missing(self, tmp_path):
        """Test verify_file_integrity for missing file."""
        result = verify_file_integrity(tmp_path / "missing.txt", "hash")
        
        assert result is False

    def test_verify_manifest_flat(self, tmp_path):
        """Test verify_manifest with a flat manifest."""
        # Create test files
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "file1.txt").write_text("content1")
        (data_dir / "file2.txt").write_text("content2")
        
        # Create manifest
        manifest_file = tmp_path / "manifest.json"
        hash1 = compute_sha256(data_dir / "file1.txt")
        hash2 = compute_sha256(data_dir / "file2.txt")
        manifest = {
            "data/file1.txt": hash1,
            "data/file2.txt": hash2,
        }
        manifest_file.write_text(json.dumps(manifest))
        
        # Verify
        results = verify_manifest(manifest_file, root=tmp_path)
        
        assert results["data/file1.txt"] is True
        assert results["data/file2.txt"] is True

    def test_verify_manifest_corruption(self, tmp_path):
        """Test verify_manifest detects corrupted files."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        test_file = data_dir / "file.txt"
        test_file.write_text("original content")
        
        manifest_file = tmp_path / "manifest.json"
        original_hash = compute_sha256(test_file)
        manifest = {"data/file.txt": original_hash}
        manifest_file.write_text(json.dumps(manifest))
        
        # Corrupt the file
        test_file.write_text("corrupted content")
        
        results = verify_manifest(manifest_file, root=tmp_path)
        
        assert results["data/file.txt"] is False


class TestWriteManifest:
    """Test manifest writing."""

    def test_write_manifest_single_file(self, tmp_path):
        """Test writing a manifest for a single file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        manifest_path = tmp_path / "manifest.json"
        entries = write_manifest([test_file], manifest_path, root=tmp_path)
        
        assert manifest_path.exists()
        assert "test.txt" in entries
        assert entries["test.txt"] == compute_sha256(test_file)

    def test_write_manifest_directory(self, tmp_path):
        """Test writing a manifest for a directory."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "file1.txt").write_text("content1")
        (data_dir / "file2.txt").write_text("content2")
        
        manifest_path = tmp_path / "manifest.json"
        entries = write_manifest([data_dir], manifest_path, root=tmp_path)
        
        assert len(entries) == 2
        assert "data/file1.txt" in entries
        assert "data/file2.txt" in entries

    def test_write_manifest_sorted(self, tmp_path):
        """Test that manifest entries are sorted."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        # Create files in non-alphabetical order
        (data_dir / "z.txt").write_text("z")
        (data_dir / "a.txt").write_text("a")
        (data_dir / "m.txt").write_text("m")
        
        manifest_path = tmp_path / "manifest.json"
        write_manifest([data_dir], manifest_path, root=tmp_path)
        
        # Load and check order
        manifest_json = json.loads(manifest_path.read_text())
        keys = list(manifest_json.keys())
        assert keys == sorted(keys)