"""
Unit tests for the state_manager module.
"""
import os
import tempfile
from pathlib import Path
import pytest
import yaml

from code.utils.state_manager import (
    compute_sha256,
    load_state,
    save_state,
    update_artifact_state,
    verify_artifact,
    update_state_for_multiple_artifacts,
)


class TestComputeSha256:
    def test_compute_sha256_known_file(self, tmp_path):
        """Test hashing a file with known content."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)

        # Known SHA-256 for "Hello, World!"
        expected_hash = (
            "315f5bdb76d078c43b8ac0064e4a0164612b1fce77c869345bfc94c75894edd3"
        )

        result = compute_sha256(test_file)
        assert result == expected_hash

    def test_compute_sha256_nonexistent_file(self, tmp_path):
        """Test hashing a file that doesn't exist."""
        non_existent = tmp_path / "does_not_exist.txt"
        with pytest.raises(FileNotFoundError):
            compute_sha256(non_existent)

    def test_compute_sha256_large_file(self, tmp_path):
        """Test hashing a larger file to ensure chunking works."""
        test_file = tmp_path / "large.txt"
        # Create a 1MB file
        content = b"A" * (1024 * 1024)
        test_file.write_bytes(content)

        result = compute_sha256(test_file)
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 hex length

class TestLoadState:
    def test_load_state_new_file(self, tmp_path):
        """Test loading state from a non-existent file."""
        state_path = tmp_path / "state.yaml"
        state = load_state(state_path)

        assert state == {"artifacts": {}, "metadata": {}}

    def test_load_state_existing_file(self, tmp_path):
        """Test loading state from an existing file."""
        state_path = tmp_path / "state.yaml"
        initial_state = {
            "artifacts": {"test.txt": {"hash": "abc123"}},
            "metadata": {"version": 1},
        }
        with open(state_path, "w") as f:
            yaml.dump(initial_state, f)

        state = load_state(state_path)
        assert state["artifacts"]["test.txt"]["hash"] == "abc123"
        assert state["metadata"]["version"] == 1

    def test_load_state_invalid_yaml(self, tmp_path):
        """Test loading state from an invalid YAML file."""
        state_path = tmp_path / "state.yaml"
        state_path.write_text("invalid: yaml: content: [")

        with pytest.raises(ValueError):
            load_state(state_path)

class TestSaveState:
    def test_save_state_creates_file(self, tmp_path):
        """Test that save_state creates the file."""
        state_path = tmp_path / "state.yaml"
        state = {"artifacts": {}, "metadata": {}}

        save_state(state, state_path)
        assert state_path.exists()

    def test_save_state_creates_directories(self, tmp_path):
        """Test that save_state creates parent directories."""
        state_path = tmp_path / "subdir" / "nested" / "state.yaml"
        state = {"artifacts": {}, "metadata": {}}

        save_state(state, state_path)
        assert state_path.exists()

    def test_save_state_valid_yaml(self, tmp_path):
        """Test that saved state is valid YAML."""
        state_path = tmp_path / "state.yaml"
        state = {"artifacts": {"test.txt": {"hash": "abc123"}}}

        save_state(state, state_path)

        with open(state_path, "r") as f:
            loaded = yaml.safe_load(f)

        assert loaded == state

class TestUpdateArtifactState:
    def test_update_artifact_state(self, tmp_path):
        """Test updating state for a single artifact."""
        artifact_path = tmp_path / "artifact.txt"
        artifact_path.write_text("Test content")
        state_path = tmp_path / "state.yaml"

        state = {"artifacts": {}, "metadata": {}}
        updated_state = update_artifact_state(artifact_path, state, state_path)

        assert "artifact.txt" in updated_state["artifacts"]
        assert "hash" in updated_state["artifacts"]["artifact.txt"]
        assert "updated_at" in updated_state["artifacts"]["artifact.txt"]
        assert "size_bytes" in updated_state["artifacts"]["artifact.txt"]
        assert updated_state["metadata"]["artifact_count"] == 1

    def test_update_artifact_state_missing_file(self, tmp_path):
        """Test updating state for a missing artifact."""
        artifact_path = tmp_path / "missing.txt"
        state_path = tmp_path / "state.yaml"
        state = {"artifacts": {}, "metadata": {}}

        with pytest.raises(FileNotFoundError):
            update_artifact_state(artifact_path, state, state_path)

class TestVerifyArtifact:
    def test_verify_artifact_match(self, tmp_path):
        """Test verifying an artifact with matching hash."""
        artifact_path = tmp_path / "test.txt"
        content = b"Test content"
        artifact_path.write_bytes(content)

        expected_hash = compute_sha256(artifact_path)
        assert verify_artifact(artifact_path, expected_hash) is True

    def test_verify_artifact_mismatch(self, tmp_path):
        """Test verifying an artifact with non-matching hash."""
        artifact_path = tmp_path / "test.txt"
        artifact_path.write_text("Test content")

        assert verify_artifact(artifact_path, "wrong_hash") is False

    def test_verify_artifact_missing(self, tmp_path):
        """Test verifying a missing artifact."""
        artifact_path = tmp_path / "missing.txt"

        with pytest.raises(FileNotFoundError):
            verify_artifact(artifact_path, "some_hash")

class TestUpdateStateForMultipleArtifacts:
    def test_update_multiple_artifacts(self, tmp_path):
        """Test updating state for multiple artifacts."""
        artifact1 = tmp_path / "art1.txt"
        artifact2 = tmp_path / "art2.txt"
        artifact1.write_text("Content 1")
        artifact2.write_text("Content 2")
        state_path = tmp_path / "state.yaml"

        state = update_state_for_multiple_artifacts(
            [artifact1, artifact2], state_path
        )

        assert "art1.txt" in state["artifacts"]
        assert "art2.txt" in state["artifacts"]
        assert state["metadata"]["artifact_count"] == 2

    def test_update_multiple_missing_artifacts(self, tmp_path):
        """Test updating state when some artifacts are missing."""
        artifact1 = tmp_path / "art1.txt"
        artifact2 = tmp_path / "missing.txt"
        artifact1.write_text("Content 1")
        state_path = tmp_path / "state.yaml"

        with pytest.raises(FileNotFoundError):
            update_state_for_multiple_artifacts(
                [artifact1, artifact2], state_path
            )