"""
Tests for the versioning module.
"""
import os
import tempfile
from pathlib import Path
import pytest
import yaml

from src.versioning import (
    compute_sha256,
    load_state,
    save_state,
    update_artifact_state,
    verify_artifact,
    PROJECT_ROOT
)


class TestComputeSha256:
    def test_compute_sha256_valid_file(self, tmp_path):
        """Test hashing a valid file."""
        test_file = tmp_path / "test.txt"
        content = "Hello, World!"
        test_file.write_text(content)

        hash_result = compute_sha256(test_file)

        assert len(hash_result) == 64  # SHA256 hex length
        assert isinstance(hash_result, str)

    def test_compute_sha256_empty_file(self, tmp_path):
        """Test hashing an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.touch()

        hash_result = compute_sha256(test_file)

        # SHA256 of empty string
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert hash_result == expected

    def test_compute_sha256_nonexistent_file(self, tmp_path):
        """Test hashing a non-existent file raises error."""
        test_file = tmp_path / "missing.txt"

        with pytest.raises(FileNotFoundError):
            compute_sha256(test_file)


class TestLoadSaveState:
    def test_load_state_nonexistent_file(self, tmp_path):
        """Test loading a non-existent state file returns empty structure."""
        state_file = tmp_path / "state.yaml"

        state = load_state(state_file)

        assert "artifacts" in state
        assert state["artifacts"] == {}

    def test_save_and_load_state(self, tmp_path):
        """Test saving and loading state."""
        state_file = tmp_path / "state.yaml"
        test_state = {
            "artifacts": {
                "data/test.csv": {
                    "hash": "abc123",
                    "path": "data/test.csv"
                }
            }
        }

        save_state(test_state, state_file)
        loaded_state = load_state(state_file)

        assert loaded_state == test_state

    def test_load_state_invalid_yaml(self, tmp_path):
        """Test loading invalid YAML raises error."""
        state_file = tmp_path / "state.yaml"
        state_file.write_text("invalid: yaml: content: [")

        with pytest.raises(ValueError):
            load_state(state_file)


class TestUpdateArtifactState:
    def test_update_artifact_state(self, tmp_path):
        """Test updating state with a new artifact."""
        state_file = tmp_path / "state.yaml"
        artifact_file = tmp_path / "artifact.txt"
        artifact_file.write_text("test content")

        # Initialize empty state
        save_state({"artifacts": {}}, state_file)

        updated_state = update_artifact_state(artifact_file, state_file)

        assert len(updated_state["artifacts"]) == 1
        key = str(artifact_file.relative_to(tmp_path))
        assert key in updated_state["artifacts"]
        assert "hash" in updated_state["artifacts"][key]
        assert updated_state["artifacts"][key]["path"] == key

    def test_update_artifact_state_with_metadata(self, tmp_path):
        """Test updating state with metadata."""
        state_file = tmp_path / "state.yaml"
        artifact_file = tmp_path / "artifact.txt"
        artifact_file.write_text("test content")

        save_state({"artifacts": {}}, state_file)

        metadata = {"source": "test_generator", "version": "1.0"}
        updated_state = update_artifact_state(
            artifact_file, state_file, metadata=metadata
        )

        key = str(artifact_file.relative_to(tmp_path))
        assert updated_state["artifacts"][key]["source"] == "test_generator"
        assert updated_state["artifacts"][key]["version"] == "1.0"

    def test_update_artifact_nonexistent(self, tmp_path):
        """Test updating state with non-existent artifact raises error."""
        state_file = tmp_path / "state.yaml"
        artifact_file = tmp_path / "missing.txt"

        save_state({"artifacts": {}}, state_file)

        with pytest.raises(FileNotFoundError):
            update_artifact_state(artifact_file, state_file)


class TestVerifyArtifact:
    def test_verify_artifact_match(self, tmp_path):
        """Test verifying an artifact with correct hash."""
        artifact_file = tmp_path / "test.txt"
        content = "verify me"
        artifact_file.write_text(content)

        correct_hash = compute_sha256(artifact_file)

        assert verify_artifact(artifact_file, correct_hash)

    def test_verify_artifact_mismatch(self, tmp_path):
        """Test verifying an artifact with wrong hash."""
        artifact_file = tmp_path / "test.txt"
        artifact_file.write_text("content")

        wrong_hash = "0" * 64

        assert not verify_artifact(artifact_file, wrong_hash)

    def test_verify_artifact_nonexistent(self, tmp_path):
        """Test verifying non-existent artifact raises error."""
        artifact_file = tmp_path / "missing.txt"

        with pytest.raises(FileNotFoundError):
            verify_artifact(artifact_file, "hash")
