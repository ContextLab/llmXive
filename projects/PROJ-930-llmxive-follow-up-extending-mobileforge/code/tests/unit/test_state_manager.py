import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from utils.state_manager import (
    initialize_state_structure,
    compute_sha256,
    register_artifact,
    verify_artifact,
    list_artifacts_by_task,
    get_state_summary,
    STATE_DIR_NAME,
    CHECKSUM_FILE,
    METADATA_FILE
)


@pytest.fixture
def temp_state_dir():
    """Create a temporary directory to act as project root."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_state_manager(temp_state_dir):
    """Initialize the state manager in the temp directory."""
    state_dir = initialize_state_structure(temp_state_dir)
    return state_dir


class TestStateDirectoryInitialization:
    def test_initialize_creates_directory(self, temp_state_dir):
        state_dir = initialize_state_structure(temp_state_dir)
        assert state_dir.exists()
        assert state_dir.name == STATE_DIR_NAME

    def test_initialize_creates_checksums_file(self, temp_state_dir):
        state_dir = initialize_state_structure(temp_state_dir)
        checksums_path = state_dir / CHECKSUM_FILE
        assert checksums_path.exists()

    def test_initialize_creates_metadata_file(self, temp_state_dir):
        state_dir = initialize_state_structure(temp_state_dir)
        metadata_path = state_dir / METADATA_FILE
        assert metadata_path.exists()

    def test_initialize_initializes_checksums_empty(self, temp_state_dir):
        initialize_state_structure(temp_state_dir)
        state_dir = temp_state_dir / STATE_DIR_NAME
        with open(state_dir / CHECKSUM_FILE, 'r') as f:
            checksums = json.load(f)
        assert checksums == {}

    def test_initialize_initializes_metadata_structure(self, temp_state_dir):
        initialize_state_structure(temp_state_dir)
        state_dir = temp_state_dir / STATE_DIR_NAME
        with open(state_dir / METADATA_FILE, 'r') as f:
            metadata = json.load(f)
        assert "version" in metadata
        assert "artifacts" in metadata
        assert isinstance(metadata["artifacts"], list)


class TestArtifactRegistration:
    def test_register_creates_checksum_entry(self, mock_state_manager, temp_state_dir):
        # Create a test file
        test_file = temp_state_dir / "test_artifact.txt"
        test_file.write_text("test content")

        # Register the artifact
        result = register_artifact(test_file, "T004", "Test artifact", temp_state_dir)

        # Verify checksums file
        state_dir = temp_state_dir / STATE_DIR_NAME
        with open(state_dir / CHECKSUM_FILE, 'r') as f:
            checksums = json.load(f)

        artifact_key = str(test_file.relative_to(temp_state_dir))
        assert artifact_key in checksums
        assert checksums[artifact_key]["task_id"] == "T004"
        assert "checksum" in checksums[artifact_key]

    def test_register_updates_metadata(self, mock_state_manager, temp_state_dir):
        test_file = temp_state_dir / "test_artifact.txt"
        test_file.write_text("test content")

        result = register_artifact(test_file, "T004", "Test artifact", temp_state_dir)

        state_dir = temp_state_dir / STATE_DIR_NAME
        with open(state_dir / METADATA_FILE, 'r') as f:
            metadata = json.load(f)

        assert len(metadata["artifacts"]) == 1
        assert metadata["artifacts"][0]["task_id"] == "T004"

    def test_register_compute_correct_checksum(self, mock_state_manager, temp_state_dir):
        test_file = temp_state_dir / "test_artifact.txt"
        content = "test content for checksum"
        test_file.write_text(content)

        result = register_artifact(test_file, "T004", "Test", temp_state_dir)

        expected_checksum = compute_sha256(test_file)
        assert result["checksum"] == expected_checksum


class TestArtifactVerification:
    def test_verify_success(self, mock_state_manager, temp_state_dir):
        test_file = temp_state_dir / "test_artifact.txt"
        test_file.write_text("test content")

        register_artifact(test_file, "T004", "Test", temp_state_dir)

        result = verify_artifact(test_file, temp_state_dir)
        assert result["verified"] is True

    def test_verify_failure_modified_file(self, mock_state_manager, temp_state_dir):
        test_file = temp_state_dir / "test_artifact.txt"
        test_file.write_text("original content")

        register_artifact(test_file, "T004", "Test", temp_state_dir)

        # Modify the file
        test_file.write_text("modified content")

        result = verify_artifact(test_file, temp_state_dir)
        assert result["verified"] is False
        assert result["registered_checksum"] != result["current_checksum"]

    def test_verify_not_registered(self, mock_state_manager, temp_state_dir):
        test_file = temp_state_dir / "test_artifact.txt"
        test_file.write_text("test content")

        result = verify_artifact(test_file, temp_state_dir)
        assert result["verified"] is False
        assert "not registered" in result["reason"]


class TestArtifactListing:
    def test_list_by_task(self, mock_state_manager, temp_state_dir):
        test_file1 = temp_state_dir / "artifact1.txt"
        test_file1.write_text("content1")

        test_file2 = temp_state_dir / "artifact2.txt"
        test_file2.write_text("content2")

        register_artifact(test_file1, "T004", "Test 1", temp_state_dir)
        register_artifact(test_file2, "T005", "Test 2", temp_state_dir)

        artifacts = list_artifacts_by_task("T004", temp_state_dir)
        assert len(artifacts) == 1
        assert artifacts[0]["task_id"] == "T004"

    def test_list_empty(self, mock_state_manager, temp_state_dir):
        artifacts = list_artifacts_by_task("T999", temp_state_dir)
        assert len(artifacts) == 0


class TestStateSummary:
    def test_summary_structure(self, mock_state_manager):
        summary = get_state_summary()
        assert "state_dir_exists" in summary
        assert "artifact_count" in summary
        assert "task_count" in summary

    def test_summary_with_artifacts(self, mock_state_manager, temp_state_dir):
        test_file = temp_state_dir / "test.txt"
        test_file.write_text("test")
        register_artifact(test_file, "T004", "Test", temp_state_dir)

        summary = get_state_summary(temp_state_dir)
        assert summary["artifact_count"] == 1
        assert summary["task_count"] == 1


class TestConstitutionPrincipleIII:
    def test_state_directory_exists(self, mock_state_manager):
        """Verify that the state directory exists as per Constitution Principle III."""
        assert mock_state_manager.exists()

    def test_checksums_tracking(self, mock_state_manager, temp_state_dir):
        """Verify that artifacts can be tracked with checksums."""
        test_file = temp_state_dir / "tracked.txt"
        test_file.write_text("tracked content")
        register_artifact(test_file, "T004", "Tracked artifact", temp_state_dir)

        result = verify_artifact(test_file, temp_state_dir)
        assert result["verified"] is True

    def test_versioning_support(self, mock_state_manager):
        """Verify that the state system supports versioning metadata."""
        state_dir = mock_state_manager
        metadata_path = state_dir / METADATA_FILE
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        assert "version" in metadata