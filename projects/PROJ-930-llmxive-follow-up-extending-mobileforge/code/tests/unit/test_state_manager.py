"""
Unit tests for the state_manager module.
Tests the setup and integrity of the `state/` directory for artifact checksums.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# We need to mock the PROJECT_ROOT to use a temporary directory for tests
# This prevents tests from polluting the actual project state directory
@pytest.fixture
def temp_state_dir(tmp_path):
    """Create a temporary state directory for testing."""
    # Create a mock project root structure
    mock_root = tmp_path / "mock_project"
    mock_root.mkdir()
    state_dir = mock_root / "state"
    state_dir.mkdir()
    return mock_root, state_dir

@pytest.fixture
def mock_state_manager(temp_state_dir):
    """
    Patch the state_manager module to use our temporary directory.
    """
    mock_root, state_dir = temp_state_dir
    
    # We need to reload the module with the patched paths
    # Since the module defines PROJECT_ROOT at import time, we patch the functions
    # that rely on it
    from utils import state_manager
    
    original_root = state_manager.PROJECT_ROOT
    original_state = state_manager.STATE_DIR
    original_manifest = state_manager.MANIFEST_PATH
    original_checksums = state_manager.CHECKSUMS_DIR

    # Patch the paths
    state_manager.PROJECT_ROOT = mock_root
    state_manager.STATE_DIR = state_dir
    state_manager.MANIFEST_PATH = state_dir / "manifest.json"
    state_manager.CHECKSUMS_DIR = state_dir / "checksums"

    yield state_manager

    # Restore original paths
    state_manager.PROJECT_ROOT = original_root
    state_manager.STATE_DIR = original_state
    state_manager.MANIFEST_PATH = original_manifest
    state_manager.CHECKSUMS_DIR = original_checksums


class TestStateDirectoryInitialization:
    """Tests for the state directory initialization logic."""

    def test_initialize_creates_directories(self, mock_state_manager, temp_state_dir):
        """Verify that initialize_state_structure creates the required directories."""
        _, state_dir = temp_state_dir
        
        # Before initialization, only the base state dir might exist (created by fixture)
        # The subdirectories should not exist yet if we clear them
        # But our fixture creates state_dir, so we check for subdirs
        
        result = mock_state_manager.initialize_state_structure()
        
        assert result is True
        assert (state_dir / "checksums").exists()
        assert (state_dir / "versions").exists()
        assert (state_dir / "manifests").exists()

    def test_initialize_creates_manifest(self, mock_state_manager, temp_state_dir):
        """Verify that initialize_state_structure creates the manifest.json file."""
        _, state_dir = temp_state_dir
        manifest_path = state_dir / "manifest.json"
        
        # Ensure manifest doesn't exist before
        if manifest_path.exists():
            manifest_path.unlink()

        mock_state_manager.initialize_state_structure()
        
        assert manifest_path.exists()
        
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        
        assert "version" in manifest
        assert "artifacts" in manifest
        assert manifest["version"] == "1.0.0"

    def test_initialize_idempotent(self, mock_state_manager, temp_state_dir):
        """Verify that calling initialize multiple times doesn't break anything."""
        _, state_dir = temp_state_dir
        
        # Initialize twice
        result1 = mock_state_manager.initialize_state_structure()
        result2 = mock_state_manager.initialize_state_structure()
        
        assert result1 is True
        assert result2 is True
        
        # Check manifest still exists and is valid
        manifest_path = state_dir / "manifest.json"
        assert manifest_path.exists()
        with open(manifest_path, "r") as f:
            json.load(f)


class TestArtifactRegistration:
    """Tests for artifact registration logic."""

    def test_register_artifact_success(self, mock_state_manager, temp_state_dir):
        """Verify successful registration of an artifact."""
        mock_root, state_dir = temp_state_dir
        
        # Create a dummy artifact file
        artifact_path = mock_root / "data" / "dummy.txt"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text("test content")

        result = mock_state_manager.register_artifact(artifact_path, "T004", "Test artifact")
        
        assert result is True
        
        # Verify manifest was updated
        manifest_path = state_dir / "manifest.json"
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        
        artifact_key = "T004_dummy.txt"
        assert artifact_key in manifest["artifacts"]
        
        entry = manifest["artifacts"][artifact_key]
        assert entry["task_id"] == "T004"
        assert entry["description"] == "Test artifact"
        assert "checksum" in entry
        assert "registered_at" in entry

    def test_register_nonexistent_file(self, mock_state_manager, temp_state_dir):
        """Verify that registering a non-existent file fails."""
        mock_root, _ = temp_state_dir
        dummy_path = mock_root / "nonexistent.txt"
        
        result = mock_state_manager.register_artifact(dummy_path, "T004", "Test")
        
        assert result is False

    def test_register_creates_checksum_file(self, mock_state_manager, temp_state_dir):
        """Verify that registration creates a standalone checksum file."""
        mock_root, state_dir = temp_state_dir
        
        # Create a dummy artifact
        artifact_path = mock_root / "data" / "test.txt"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text("content for checksum")

        mock_state_manager.register_artifact(artifact_path, "T004", "Test")
        
        # Check for checksum file
        checksum_file = state_dir / "checksums" / "T004_test.txt.sha256"
        assert checksum_file.exists()
        
        with open(checksum_file, "r") as f:
            content = f.read().strip()
        
        # Format should be: <hash>  <filename>
        assert "  " in content
        assert content.endswith("test.txt")


class TestArtifactVerification:
    """Tests for artifact verification logic."""

    def test_verify_integrity(self, mock_state_manager, temp_state_dir):
        """Verify that verification works for an unmodified artifact."""
        mock_root, state_dir = temp_state_dir
        
        # Create and register an artifact
        artifact_path = mock_root / "data" / "verify.txt"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text("original content")
        
        mock_state_manager.register_artifact(artifact_path, "T004", "Verification test")
        
        # Verify should pass
        result = mock_state_manager.verify_artifact(artifact_path, "T004")
        assert result is True

    def test_verify_detects_modification(self, mock_state_manager, temp_state_dir):
        """Verify that modification of an artifact is detected."""
        mock_root, state_dir = temp_state_dir
        
        # Create and register an artifact
        artifact_path = mock_root / "data" / "modify.txt"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text("original content")
        
        mock_state_manager.register_artifact(artifact_path, "T004", "Modification test")
        
        # Modify the file
        artifact_path.write_text("modified content")
        
        # Verify should fail
        result = mock_state_manager.verify_artifact(artifact_path, "T004")
        assert result is False

    def test_verify_missing_artifact(self, mock_state_manager, temp_state_dir):
        """Verify that missing artifacts are handled correctly."""
        mock_root, _ = temp_state_dir
        dummy_path = mock_root / "missing.txt"
        
        result = mock_state_manager.verify_artifact(dummy_path, "T004")
        assert result is False


class TestArtifactListing:
    """Tests for listing artifacts by task."""

    def test_list_by_task(self, mock_state_manager, temp_state_dir):
        """Verify listing artifacts for a specific task."""
        mock_root, state_dir = temp_state_dir
        
        # Register artifacts for T004 and T005
        for i in range(3):
            artifact_path = mock_root / "data" / f"file_{i}.txt"
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            artifact_path.write_text(f"content {i}")
            
            task_id = "T004" if i < 2 else "T005"
            mock_state_manager.register_artifact(artifact_path, task_id, f"Test {i}")
        
        # List for T004
        artifacts = mock_state_manager.list_artifacts_by_task("T004")
        assert len(artifacts) == 2
        assert all(a["task_id"] == "T004" for a in artifacts)

    def test_list_empty_task(self, mock_state_manager, temp_state_dir):
        """Verify listing returns empty list for task with no artifacts."""
        _, _ = temp_state_dir
        
        artifacts = mock_state_manager.list_artifacts_by_task("NONEXISTENT")
        assert artifacts == []


class TestStateSummary:
    """Tests for state summary generation."""

    def test_get_summary(self, mock_state_manager, temp_state_dir):
        """Verify state summary contains expected fields."""
        mock_root, state_dir = temp_state_dir
        
        # Register an artifact
        artifact_path = mock_root / "data" / "summary.txt"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text("test")
        mock_state_manager.register_artifact(artifact_path, "T004", "Summary test")
        
        summary = mock_state_manager.get_state_summary()
        
        assert "total_artifacts" in summary
        assert "tasks" in summary
        assert summary["total_artifacts"] == 1
        assert "T004" in summary["tasks"]
