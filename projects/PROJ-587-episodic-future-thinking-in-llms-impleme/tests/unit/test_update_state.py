"""
Unit tests for update_state.py (Constitution Principle V).
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.update_state import (
    compute_file_hash,
    load_state,
    save_state,
    update_artifact,
    verify_artifact,
    get_artifact_info,
    list_artifacts,
    STATE_FILE,
    PROJECT_ROOT,
)


class TestComputeFileHash:
    """Tests for compute_file_hash function."""

    def test_hash_computation(self, tmp_path):
        """Test that hash is computed correctly for a simple file."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)

        hash_val = compute_file_hash(test_file)

        # SHA-256 of "Hello, World!"
        expected_hash = "315f5bdb76d078c43b8ac0064e4a0164612b1fce77c869345bfc94c75894edd3"
        assert hash_val == expected_hash

    def test_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for non-existent file."""
        non_existent = tmp_path / "does_not_exist.txt"

        with pytest.raises(FileNotFoundError):
            compute_file_hash(non_existent)

    def test_directory_raises_error(self, tmp_path):
        """Test that IsADirectoryError is raised for directories."""
        with pytest.raises(IsADirectoryError):
            compute_file_hash(tmp_path)


class TestLoadSaveState:
    """Tests for load_state and save_state functions."""

    def test_load_nonexistent_state(self, tmp_path, monkeypatch):
        """Test loading when state file doesn't exist."""
        # Mock STATE_FILE to point to a non-existent file
        mock_state_file = tmp_path / "nonexistent_state.json"
        monkeypatch.setattr("utils.update_state.STATE_FILE", mock_state_file)

        state = load_state()

        assert "artifacts" in state
        assert "last_updated" in state
        assert "version" in state
        assert state["artifacts"] == {}

    def test_save_and_load_state(self, tmp_path, monkeypatch):
        """Test saving and loading state."""
        mock_state_file = tmp_path / "test_state.json"
        monkeypatch.setattr("utils.update_state.STATE_FILE", mock_state_file)

        test_state = {
            "artifacts": {
                "test.txt": {"hash": "abc123", "type": "test"}
            },
            "version": "1.0"
        }

        save_state(test_state)
        loaded_state = load_state()

        assert loaded_state["artifacts"]["test.txt"]["hash"] == "abc123"
        assert loaded_state["last_updated"] is not None


class TestUpdateArtifact:
    """Tests for update_artifact function."""

    def test_update_existing_artifact(self, tmp_path, monkeypatch):
        """Test updating an existing artifact."""
        # Setup mock paths
        mock_state_file = tmp_path / "state.json"
        mock_project_root = tmp_path / "project"
        mock_project_root.mkdir()

        monkeypatch.setattr("utils.update_state.STATE_FILE", mock_state_file)
        monkeypatch.setattr("utils.update_state.PROJECT_ROOT", mock_project_root)

        # Create a test artifact
        test_artifact = mock_project_root / "data" / "test.txt"
        test_artifact.parent.mkdir()
        test_artifact.write_text("Test content")

        # Update the artifact
        key, hash_val = update_artifact(test_artifact, "data")

        assert key == "data/test.txt"
        assert hash_val is not None
        assert len(hash_val) == 64  # SHA-256 hex length

        # Verify state was saved
        state = load_state()
        assert "data/test.txt" in state["artifacts"]
        assert state["artifacts"]["data/test.txt"]["type"] == "data"

    def test_update_with_metadata(self, tmp_path, monkeypatch):
        """Test updating artifact with custom metadata."""
        mock_state_file = tmp_path / "state.json"
        mock_project_root = tmp_path / "project"
        mock_project_root.mkdir()

        monkeypatch.setattr("utils.update_state.STATE_FILE", mock_state_file)
        monkeypatch.setattr("utils.update_state.PROJECT_ROOT", mock_project_root)

        test_artifact = mock_project_root / "test.txt"
        test_artifact.write_text("Content")

        metadata = {"author": "test", "version": "1.0"}
        key, _ = update_artifact(test_artifact, "script", metadata)

        state = load_state()
        assert state["artifacts"][key]["metadata"]["author"] == "test"

    def test_update_nonexistent_artifact(self, tmp_path, monkeypatch):
        """Test that FileNotFoundError is raised for non-existent artifact."""
        mock_state_file = tmp_path / "state.json"
        mock_project_root = tmp_path / "project"
        mock_project_root.mkdir()

        monkeypatch.setattr("utils.update_state.STATE_FILE", mock_state_file)
        monkeypatch.setattr("utils.update_state.PROJECT_ROOT", mock_project_root)

        non_existent = mock_project_root / "does_not_exist.txt"

        with pytest.raises(FileNotFoundError):
            update_artifact(non_existent, "test")


class TestVerifyArtifact:
    """Tests for verify_artifact function."""

    def test_verify_valid_artifact(self, tmp_path, monkeypatch):
        """Test verification of a valid artifact."""
        mock_state_file = tmp_path / "state.json"
        mock_project_root = tmp_path / "project"
        mock_project_root.mkdir()

        monkeypatch.setattr("utils.update_state.STATE_FILE", mock_state_file)
        monkeypatch.setattr("utils.update_state.PROJECT_ROOT", mock_project_root)

        test_artifact = mock_project_root / "test.txt"
        test_artifact.write_text("Content")

        # First update to register the artifact
        update_artifact(test_artifact, "test")

        # Then verify
        assert verify_artifact(test_artifact) is True

    def test_verify_modified_artifact(self, tmp_path, monkeypatch):
        """Test verification fails after artifact modification."""
        mock_state_file = tmp_path / "state.json"
        mock_project_root = tmp_path / "project"
        mock_project_root.mkdir()

        monkeypatch.setattr("utils.update_state.STATE_FILE", mock_state_file)
        monkeypatch.setattr("utils.update_state.PROJECT_ROOT", mock_project_root)

        test_artifact = mock_project_root / "test.txt"
        test_artifact.write_text("Original")

        # Register original
        update_artifact(test_artifact, "test")

        # Modify the file
        test_artifact.write_text("Modified")

        # Verification should fail
        assert verify_artifact(test_artifact) is False

    def test_verify_nonexistent_artifact(self, tmp_path, monkeypatch):
        """Test verification of non-existent file."""
        mock_state_file = tmp_path / "state.json"
        mock_project_root = tmp_path / "project"
        mock_project_root.mkdir()

        monkeypatch.setattr("utils.update_state.STATE_FILE", mock_state_file)
        monkeypatch.setattr("utils.update_state.PROJECT_ROOT", mock_project_root)

        non_existent = mock_project_root / "does_not_exist.txt"

        assert verify_artifact(non_existent) is False


class TestGetArtifactInfo:
    """Tests for get_artifact_info function."""

    def test_get_existing_artifact_info(self, tmp_path, monkeypatch):
        """Test retrieving info for an existing artifact."""
        mock_state_file = tmp_path / "state.json"
        mock_project_root = tmp_path / "project"
        mock_project_root.mkdir()

        monkeypatch.setattr("utils.update_state.STATE_FILE", mock_state_file)
        monkeypatch.setattr("utils.update_state.PROJECT_ROOT", mock_project_root)

        test_artifact = mock_project_root / "test.txt"
        test_artifact.write_text("Content")

        update_artifact(test_artifact, "test", {"custom": "value"})

        info = get_artifact_info(test_artifact)

        assert info is not None
        assert info["type"] == "test"
        assert info["metadata"]["custom"] == "value"

    def test_get_nonexistent_artifact_info(self, tmp_path, monkeypatch):
        """Test retrieving info for non-existent artifact."""
        mock_state_file = tmp_path / "state.json"
        mock_project_root = tmp_path / "project"
        mock_project_root.mkdir()

        monkeypatch.setattr("utils.update_state.STATE_FILE", mock_state_file)
        monkeypatch.setattr("utils.update_state.PROJECT_ROOT", mock_project_root)

        non_existent = mock_project_root / "does_not_exist.txt"

        info = get_artifact_info(non_existent)
        assert info is None


class TestListArtifacts:
    """Tests for list_artifacts function."""

    def test_list_all_artifacts(self, tmp_path, monkeypatch):
        """Test listing all artifacts."""
        mock_state_file = tmp_path / "state.json"
        mock_project_root = tmp_path / "project"
        mock_project_root.mkdir()

        monkeypatch.setattr("utils.update_state.STATE_FILE", mock_state_file)
        monkeypatch.setattr("utils.update_state.PROJECT_ROOT", mock_project_root)

        # Create and register multiple artifacts
        for i in range(3):
            test_artifact = mock_project_root / f"test_{i}.txt"
            test_artifact.write_text(f"Content {i}")
            update_artifact(test_artifact, "test")

        artifacts = list_artifacts()

        assert len(artifacts) == 3

    def test_list_by_type(self, tmp_path, monkeypatch):
        """Test filtering artifacts by type."""
        mock_state_file = tmp_path / "state.json"
        mock_project_root = tmp_path / "project"
        mock_project_root.mkdir()

        monkeypatch.setattr("utils.update_state.STATE_FILE", mock_state_file)
        monkeypatch.setattr("utils.update_state.PROJECT_ROOT", mock_project_root)

        # Create artifacts with different types
        script = mock_project_root / "script.py"
        script.write_text("print('hi')")
        update_artifact(script, "script")

        data = mock_project_root / "data.csv"
        data.write_text("col1,col2")
        update_artifact(data, "data")

        scripts = list_artifacts(artifact_type="script")
        data_list = list_artifacts(artifact_type="data")

        assert len(scripts) == 1
        assert len(data_list) == 1
        assert "script.py" in scripts
        assert "data.csv" in data_list