"""
Unit tests for hygiene utilities (SHA-256 hashing and state management).
"""
import os
import tempfile
from pathlib import Path

import pytest
import yaml

# Adjust import path based on project structure
# Assuming code/utils/hygiene.py is the module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.hygiene import (
    calculate_sha256,
    load_state,
    save_state,
    update_state_checksum,
    verify_checksum,
)


class TestCalculateSha256:
    def test_hash_correctness(self, tmp_path):
        """Verify SHA-256 hash is correct for known content."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)

        # Known SHA-256 for "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        result = calculate_sha256(str(test_file))

        assert result == expected

    def test_file_not_found(self, tmp_path):
        """Verify FileNotFoundError is raised for missing file."""
        non_existent = tmp_path / "missing.txt"
        with pytest.raises(FileNotFoundError):
            calculate_sha256(str(non_existent))

    def test_binary_content(self, tmp_path):
        """Verify hash works for binary content."""
        test_file = tmp_path / "binary.bin"
        content = bytes(range(256))
        test_file.write_bytes(content)

        result = calculate_sha256(str(test_file))
        assert len(result) == 64  # SHA-256 hex length


class TestStateManagement:
    def test_load_state_empty_file(self, tmp_path):
        """Load state from non-existent file returns empty dict."""
        state_file = tmp_path / "state.yaml"
        result = load_state(str(state_file))
        assert result == {}

    def test_load_state_valid_yaml(self, tmp_path):
        """Load state from valid YAML file."""
        state_file = tmp_path / "state.yaml"
        data = {"key": "value", "number": 42}
        with open(state_file, "w") as f:
            yaml.dump(data, f)

        result = load_state(str(state_file))
        assert result == data

    def test_save_state(self, tmp_path):
        """Save state creates file with correct content."""
        state_file = tmp_path / "state.yaml"
        data = {"test": "data"}
        save_state(str(state_file), data)

        assert state_file.exists()
        with open(state_file, "r") as f:
            loaded = yaml.safe_load(f)
        assert loaded == data

    def test_save_state_creates_dirs(self, tmp_path):
        """Save state creates parent directories if they don't exist."""
        state_file = tmp_path / "sub" / "dir" / "state.yaml"
        data = {"test": "data"}
        save_state(str(state_file), data)

        assert state_file.exists()


class TestUpdateStateChecksum:
    def test_update_creates_structure(self, tmp_path):
        """Update checksum creates state file with correct structure."""
        state_file = tmp_path / "state.yaml"
        artifact_file = tmp_path / "artifact.txt"
        artifact_file.write_text("content")

        update_state_checksum(str(state_file), str(artifact_file))

        state = load_state(str(state_file))
        assert "checksums" in state
        assert "artifact.txt" in state["checksums"]

    def test_update_stores_hash(self, tmp_path):
        """Update checksum stores the correct hash."""
        state_file = tmp_path / "state.yaml"
        artifact_file = tmp_path / "artifact.txt"
        artifact_file.write_bytes(b"test")

        update_state_checksum(str(state_file), str(artifact_file))

        state = load_state(str(state_file))
        stored_hash = state["checksums"]["artifact.txt"]["hash"]
        calculated = calculate_sha256(str(artifact_file))

        assert stored_hash == calculated

    def test_update_overwrites_existing(self, tmp_path):
        """Update checksum overwrites existing entry."""
        state_file = tmp_path / "state.yaml"
        artifact_file = tmp_path / "artifact.txt"

        # First update
        artifact_file.write_text("v1")
        update_state_checksum(str(state_file), str(artifact_file))

        # Second update with different content
        artifact_file.write_text("v2")
        update_state_checksum(str(state_file), str(artifact_file))

        state = load_state(str(state_file))
        # Hash should match v2, not v1
        assert state["checksums"]["artifact.txt"]["hash"] == calculate_sha256(str(artifact_file))


class TestVerifyChecksum:
    def test_verify_success(self, tmp_path):
        """Verify returns True when checksum matches."""
        state_file = tmp_path / "state.yaml"
        artifact_file = tmp_path / "artifact.txt"
        artifact_file.write_text("content")

        update_state_checksum(str(state_file), str(artifact_file))
        assert verify_checksum(str(state_file), str(artifact_file)) is True

    def test_verify_failure_modified(self, tmp_path):
        """Verify returns False when file is modified."""
        state_file = tmp_path / "state.yaml"
        artifact_file = tmp_path / "artifact.txt"
        artifact_file.write_text("original")

        update_state_checksum(str(state_file), str(artifact_file))

        # Modify file
        artifact_file.write_text("modified")

        assert verify_checksum(str(state_file), str(artifact_file)) is False

    def test_verify_missing_state(self, tmp_path):
        """Verify returns False if artifact not in state."""
        state_file = tmp_path / "state.yaml"
        artifact_file = tmp_path / "artifact.txt"
        artifact_file.write_text("content")

        # Don't update state
        assert verify_checksum(str(state_file), str(artifact_file)) is False

    def test_verify_missing_file(self, tmp_path):
        """Verify returns False if artifact file is missing."""
        state_file = tmp_path / "state.yaml"
        artifact_file = tmp_path / "artifact.txt"
        artifact_file.write_text("content")

        update_state_checksum(str(state_file), str(artifact_file))

        # Delete file
        artifact_file.unlink()

        assert verify_checksum(str(state_file), str(artifact_file)) is False
