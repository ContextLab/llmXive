"""
Unit tests for checksum_utils module.
"""
import os
import tempfile
import yaml
from pathlib import Path
import pytest
from src.utils.checksum_utils import (
    compute_file_sha256,
    load_state_file,
    save_state_file,
    update_artifact_hash,
    compute_artifact_hashes
)

class TestChecksumUtils:
    """Test cases for checksum utility functions."""

    def test_compute_file_sha256(self, tmp_path):
        """Test SHA-256 computation for a simple file."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)

        hash_result = compute_file_sha256(test_file)

        # Known SHA-256 hash for "Hello, World!"
        expected_hash = "7f83b1657ff1fc53b92dc18148a1d65dfa671d0c1a1d2b0b3b3b3b3b3b3b3b3b"
        # Actually compute expected for verification
        import hashlib
        expected_hash = hashlib.sha256(test_content).hexdigest()

        assert hash_result == expected_hash
        assert len(hash_result) == 64  # SHA-256 hex length

    def test_compute_file_sha256_empty(self, tmp_path):
        """Test SHA-256 computation for an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")

        hash_result = compute_file_sha256(test_file)
        expected_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

        assert hash_result == expected_hash

    def test_compute_file_sha256_nonexistent(self, tmp_path):
        """Test that FileNotFoundError is raised for non-existent file."""
        nonexistent = tmp_path / "does_not_exist.txt"

        with pytest.raises(FileNotFoundError):
            compute_file_sha256(nonexistent)

    def test_load_state_file_existing(self, tmp_path):
        """Test loading an existing state file."""
        state_file = tmp_path / "state.yaml"
        initial_data = {
            "project_id": "TEST-001",
            "artifact_hashes": {"file1.txt": {"hash": "abc123"}}
        }
        with open(state_file, "w") as f:
            yaml.safe_dump(initial_data, f)

        result = load_state_file(state_file)

        assert result["project_id"] == "TEST-001"
        assert "file1.txt" in result["artifact_hashes"]

    def test_load_state_file_nonexistent(self, tmp_path):
        """Test loading a non-existent state file creates default structure."""
        state_file = tmp_path / "nonexistent.yaml"

        result = load_state_file(state_file)

        assert "project_id" in result
        assert "artifact_hashes" in result
        assert result["artifact_hashes"] == {}

    def test_save_state_file(self, tmp_path):
        """Test saving state file."""
        state_file = tmp_path / "state.yaml"
        data = {
            "project_id": "TEST-002",
            "artifact_hashes": {"file.txt": {"hash": "def456", "algorithm": "sha256"}}
        }

        save_state_file(state_file, data)

        assert state_file.exists()
        with open(state_file, "r") as f:
            loaded = yaml.safe_load(f)

        assert loaded["project_id"] == "TEST-002"
        assert "file.txt" in loaded["artifact_hashes"]

    def test_update_artifact_hash(self, tmp_path):
        """Test updating artifact hash in state."""
        state = {"artifact_hashes": {}}
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        hash_value = compute_file_sha256(test_file)
        updated_state = update_artifact_hash(state, test_file, hash_value)

        assert len(updated_state["artifact_hashes"]) == 1
        # Check that the hash is stored (path might be relative)
        assert any(v.get("hash") == hash_value for v in updated_state["artifact_hashes"].values())

    def test_compute_artifact_hashes(self, tmp_path):
        """Test computing hashes for multiple files."""
        # Create test structure
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "file1.py").write_text("print('hello')")
        (src_dir / "file2.py").write_text("print('world')")
        (tmp_path / "readme.md").write_text("# Readme")

        state_file = tmp_path / "state.yaml"
        state_file.write_text("project_id: TEST-003\nartifact_hashes: {}\n")

        result = compute_artifact_hashes(tmp_path, state_file, exclude_patterns=["*.md"])

        # Should have computed hashes for .py files only (excluded .md)
        assert len(result["artifact_hashes"]) == 2

        # Verify hashes are valid SHA-256
        for path, info in result["artifact_hashes"].items():
            assert len(info["hash"]) == 64
            assert info["algorithm"] == "sha256"