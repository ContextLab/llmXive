"""
Tests for the update_state utility module.

These tests verify:
1. SHA-256 hash computation is correct
2. State file creation and updates work properly
3. Artifact and task state tracking functions correctly
4. Error handling for missing files
"""

import os
import tempfile
import yaml
from pathlib import Path
import pytest

from utils.update_state import (
    compute_sha256,
    load_state,
    save_state,
    update_artifact_state,
    update_task_state,
    hash_multiple_artifacts,
    get_artifact_hash,
    verify_artifact_integrity,
)


class TestSHA256Hashing:
    """Tests for SHA-256 hash computation."""

    def test_compute_sha256_known_value(self, tmp_path):
        """Test hash computation against a known value."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        # Known SHA-256 hash for "Hello, World!"
        expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"

        actual_hash = compute_sha256(str(test_file))
        assert actual_hash == expected_hash

    def test_compute_sha256_empty_file(self, tmp_path):
        """Test hash computation for an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.touch()

        # Known SHA-256 hash for empty string
        expected_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

        actual_hash = compute_sha256(str(test_file))
        assert actual_hash == expected_hash

    def test_compute_sha256_file_not_found(self):
        """Test that FileNotFoundError is raised for missing files."""
        with pytest.raises(FileNotFoundError):
            compute_sha256("/nonexistent/path/file.txt")

    def test_compute_sha256_large_file(self, tmp_path):
        """Test hash computation for a larger file."""
        test_file = tmp_path / "large.txt"
        content = "x" * 1000000  # 1MB of data
        test_file.write_text(content)

        actual_hash = compute_sha256(str(test_file))
        assert len(actual_hash) == 64  # SHA-256 produces 64 hex characters
        assert all(c in "0123456789abcdef" for c in actual_hash)


class TestStateManagement:
    """Tests for state file management."""

    def test_load_state_new_file(self, tmp_path):
        """Test loading a state file that doesn't exist yet."""
        state_path = tmp_path / "new_state.yaml"

        state = load_state(str(state_path))

        assert state["pipeline_version"] == "1.0.0"
        assert "artifacts" in state
        assert "tasks" in state
        assert "metadata" in state

    def test_load_state_existing_file(self, tmp_path):
        """Test loading an existing state file."""
        state_path = tmp_path / "existing_state.yaml"

        initial_state = {
            "pipeline_version": "1.0.0",
            "artifacts": {"test.txt": {"hash": "abc123"}},
            "tasks": {"T001": {"status": "completed"}}
        }

        with open(state_path, "w") as f:
            yaml.dump(initial_state, f)

        loaded_state = load_state(str(state_path))

        assert loaded_state["pipeline_version"] == "1.0.0"
        assert "test.txt" in loaded_state["artifacts"]
        assert "T001" in loaded_state["tasks"]

    def test_save_state_creates_directory(self, tmp_path):
        """Test that save_state creates parent directories if needed."""
        state_path = tmp_path / "subdir" / "nested" / "state.yaml"

        state = {"test": "data"}
        save_state(state, str(state_path))

        assert state_path.exists()

    def test_save_state_updates_timestamp(self, tmp_path):
        """Test that save_state updates the last_updated field."""
        state_path = tmp_path / "state.yaml"

        state = {"pipeline_version": "1.0.0"}
        save_state(state, str(state_path))

        loaded_state = load_state(str(state_path))
        assert loaded_state["last_updated"] is not None


class TestArtifactStateTracking:
    """Tests for artifact state tracking."""

    def test_update_artifact_state(self, tmp_path):
        """Test updating state with a new artifact."""
        artifact_path = tmp_path / "artifact.txt"
        artifact_path.write_text("test content")
        state_path = tmp_path / "state.yaml"

        state = update_artifact_state(
            str(artifact_path),
            str(state_path),
            artifact_name="custom_name.txt",
            task_id="T005",
            metadata={"source": "test"}
        )

        assert "custom_name.txt" in state["artifacts"]
        artifact_info = state["artifacts"]["custom_name.txt"]
        assert artifact_info["task_id"] == "T005"
        assert artifact_info["metadata"]["source"] == "test"
        assert len(artifact_info["hash"]) == 64
        assert artifact_info["size_bytes"] == len("test content")

    def test_update_artifact_state_auto_name(self, tmp_path):
        """Test that artifact name defaults to filename."""
        artifact_path = tmp_path / "auto_named.txt"
        artifact_path.write_text("content")
        state_path = tmp_path / "state.yaml"

        state = update_artifact_state(
            str(artifact_path),
            str(state_path)
        )

        assert "auto_named.txt" in state["artifacts"]

    def test_update_artifact_state_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing artifacts."""
        state_path = tmp_path / "state.yaml"

        with pytest.raises(FileNotFoundError):
            update_artifact_state(
                str(tmp_path / "nonexistent.txt"),
                str(state_path)
            )


class TestTaskStateTracking:
    """Tests for task state tracking."""

    def test_update_task_state(self, tmp_path):
        """Test updating task status in state."""
        state_path = tmp_path / "state.yaml"

        state = update_task_state(
            "T005",
            "completed",
            str(state_path),
            details={"duration": 120}
        )

        assert "T005" in state["tasks"]
        assert state["tasks"]["T005"]["status"] == "completed"
        assert state["tasks"]["T005"]["details"]["duration"] == 120

    def test_update_task_state_overwrites_existing(self, tmp_path):
        """Test that task status can be updated."""
        state_path = tmp_path / "state.yaml"

        update_task_state("T005", "running", str(state_path))
        state = update_task_state("T005", "completed", str(state_path))

        assert state["tasks"]["T005"]["status"] == "completed"


class TestMultipleArtifacts:
    """Tests for handling multiple artifacts."""

    def test_hash_multiple_artifacts(self, tmp_path):
        """Test hashing multiple artifacts at once."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        state_path = tmp_path / "state.yaml"

        file1.write_text("content1")
        file2.write_text("content2")

        state = hash_multiple_artifacts(
            [str(file1), str(file2)],
            str(state_path),
            task_id="T005"
        )

        assert "file1.txt" in state["artifacts"]
        assert "file2.txt" in state["artifacts"]
        assert state["artifacts"]["file1.txt"]["task_id"] == "T005"

    def test_hash_multiple_artifacts_skips_missing(self, tmp_path):
        """Test that missing files are skipped without error."""
        file1 = tmp_path / "existing.txt"
        file2 = tmp_path / "missing.txt"
        state_path = tmp_path / "state.yaml"

        file1.write_text("content")

        state = hash_multiple_artifacts(
            [str(file1), str(file2)],
            str(state_path)
        )

        assert "existing.txt" in state["artifacts"]
        assert "missing.txt" not in state["artifacts"]


class TestVerification:
    """Tests for artifact verification."""

    def test_get_artifact_hash(self, tmp_path):
        """Test getting hash without updating state."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("verification test")

        hash_value = get_artifact_hash(str(test_file))

        assert len(hash_value) == 64
        assert all(c in "0123456789abcdef" for c in hash_value)

    def test_verify_artifact_integrity_success(self, tmp_path):
        """Test successful verification."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("verification test")

        actual_hash = compute_sha256(str(test_file))
        is_valid = verify_artifact_integrity(str(test_file), actual_hash)

        assert is_valid is True

    def test_verify_artifact_integrity_failure(self, tmp_path):
        """Test failed verification with wrong hash."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("verification test")

        wrong_hash = "a" * 64
        is_valid = verify_artifact_integrity(str(test_file), wrong_hash)

        assert is_valid is False