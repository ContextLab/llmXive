"""
Unit tests for the update_state module.

Tests cover file hashing, artifact scanning, manifest generation,
and state integrity verification.
"""
import json
import os
import tempfile
import shutil
from pathlib import Path
import pytest

from code.utils.update_state import (
    compute_file_hash,
    get_git_commit_hash,
    scan_artifacts,
    update_state_manifest,
    verify_state_integrity
)


class TestComputeFileHash:
    """Tests for the compute_file_hash function."""

    def test_hash_consistency(self, tmp_path):
        """Verify that hashing the same file twice yields the same result."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        
        hash1 = compute_file_hash(str(test_file))
        hash2 = compute_file_hash(str(test_file))
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex digest length

    def test_hash_changes_with_content(self, tmp_path):
        """Verify that different content produces different hashes."""
        test_file = tmp_path / "test.txt"
        
        test_file.write_text("Content A")
        hash_a = compute_file_hash(str(test_file))
        
        test_file.write_text("Content B")
        hash_b = compute_file_hash(str(test_file))
        
        assert hash_a != hash_b

    def test_file_not_found(self, tmp_path):
        """Verify that hashing a non-existent file raises FileNotFoundError."""
        non_existent = tmp_path / "does_not_exist.txt"
        
        with pytest.raises(FileNotFoundError):
            compute_file_hash(str(non_existent))

    def test_binary_file_hash(self, tmp_path):
        """Verify hashing works for binary files."""
        test_file = tmp_path / "binary.bin"
        test_file.write_bytes(b"\x00\x01\x02\x03\x04")
        
        hash_val = compute_file_hash(str(test_file))
        assert len(hash_val) == 64


class TestScanArtifacts:
    """Tests for the scan_artifacts function."""

    def test_scan_empty_directory(self, tmp_path):
        """Verify scanning an empty directory returns an empty list."""
        artifacts = scan_artifacts(str(tmp_path))
        assert artifacts == []

    def test_scan_single_file(self, tmp_path):
        """Verify scanning a directory with one file."""
        test_file = tmp_path / "test.csv"
        test_file.write_text("a,b\n1,2")
        
        artifacts = scan_artifacts(str(tmp_path))
        
        assert len(artifacts) == 1
        assert artifacts[0]["path"] == "test.csv"
        assert artifacts[0]["size_bytes"] > 0
        assert "hash_sha256" in artifacts[0]

    def test_scan_recursive(self, tmp_path):
        """Verify recursive scanning of subdirectories."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        
        file1 = tmp_path / "file1.csv"
        file1.write_text("data")
        
        file2 = subdir / "file2.csv"
        file2.write_text("more data")
        
        artifacts = scan_artifacts(str(tmp_path))
        
        assert len(artifacts) == 2
        paths = [a["path"] for a in artifacts]
        assert "file1.csv" in paths
        assert "subdir/file2.csv" in paths

    def test_extension_filter(self, tmp_path):
        """Verify filtering by file extension."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("text")
        
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("csv")
        
        artifacts = scan_artifacts(str(tmp_path), extensions=[".csv"])
        
        assert len(artifacts) == 1
        assert artifacts[0]["path"] == "test.csv"


class TestUpdateStateManifest:
    """Tests for the update_state_manifest function."""

    def test_create_manifest(self, tmp_path):
        """Verify creating a new manifest file."""
        output_path = tmp_path / "manifest.json"
        artifacts = [
            {"path": "test.csv", "size_bytes": 10, "hash_sha256": "abc123"}
        ]
        
        result_path = update_state_manifest(
            str(output_path),
            artifacts,
            git_hash="abc1234"
        )
        
        assert os.path.exists(result_path)
        
        with open(result_path, "r") as f:
            manifest = json.load(f)
        
        assert "timestamp" in manifest
        assert manifest["git_commit"] == "abc1234"
        assert manifest["total_artifacts"] == 1
        assert manifest["artifacts"][0]["path"] == "test.csv"

    def test_atomic_write(self, tmp_path):
        """Verify that writing is atomic (no .tmp file left behind)."""
        output_path = tmp_path / "manifest.json"
        artifacts = [{"path": "test.csv", "size_bytes": 10, "hash_sha256": "abc123"}]
        
        update_state_manifest(str(output_path), artifacts)
        
        # Ensure no temporary file remains
        temp_path = output_path.with_suffix(".tmp")
        assert not temp_path.exists()


class TestVerifyStateIntegrity:
    """Tests for the verify_state_integrity function."""

    def test_verify_valid_state(self, tmp_path):
        """Verify integrity check passes for valid state."""
        # Create a test file
        test_file = tmp_path / "test.csv"
        test_file.write_text("data")
        
        # Create a manifest with correct hash
        file_hash = compute_file_hash(str(test_file))
        artifacts = [
            {
                "path": "test.csv",
                "hash_sha256": file_hash,
                "size_bytes": 4
            }
        ]
        
        manifest_path = tmp_path / "manifest.json"
        update_state_manifest(str(manifest_path), artifacts)
        
        is_valid, errors = verify_state_integrity(str(manifest_path), str(tmp_path))
        
        assert is_valid is True
        assert len(errors) == 0

    def test_verify_missing_file(self, tmp_path):
        """Verify integrity check fails for missing file."""
        artifacts = [
            {
                "path": "missing.csv",
                "hash_sha256": "abc123",
                "size_bytes": 10
            }
        ]
        
        manifest_path = tmp_path / "manifest.json"
        update_state_manifest(str(manifest_path), artifacts)
        
        is_valid, errors = verify_state_integrity(str(manifest_path), str(tmp_path))
        
        assert is_valid is False
        assert any("missing.csv" in err for err in errors)

    def test_verify_hash_mismatch(self, tmp_path):
        """Verify integrity check fails when file content changes."""
        test_file = tmp_path / "test.csv"
        test_file.write_text("original")
        
        file_hash = compute_file_hash(str(test_file))
        artifacts = [
            {
                "path": "test.csv",
                "hash_sha256": file_hash,
                "size_bytes": 8
            }
        ]
        
        manifest_path = tmp_path / "manifest.json"
        update_state_manifest(str(manifest_path), artifacts)
        
        # Modify the file
        test_file.write_text("modified content")
        
        is_valid, errors = verify_state_integrity(str(manifest_path), str(tmp_path))
        
        assert is_valid is False
        assert any("Hash mismatch" in err for err in errors)

    def test_verify_nonexistent_manifest(self, tmp_path):
        """Verify integrity check fails for missing manifest."""
        is_valid, errors = verify_state_integrity(
            str(tmp_path / "nonexistent.json")
        )
        
        assert is_valid is False
        assert len(errors) == 1
        assert "not found" in errors[0].lower()