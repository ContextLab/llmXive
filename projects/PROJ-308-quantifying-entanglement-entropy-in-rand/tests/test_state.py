"""
Tests for state management and metadata logging (Task T011, T012).
"""
import json
import os
import pytest
from pathlib import Path
from datetime import datetime

# Adjust imports based on project structure
import sys
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from state_manager import (
    log_unresolved_realization,
    log_unresolved_batch,
    get_unresolved_summary,
    clear_unresolved_log,
    get_unresolved_by_delta,
    get_unresolved_by_reason,
    _load_metadata,
    _load_unresolved_log,
    METADATA_FILE,
    UNRESOLVED_LOG_FILE
)
from state_utils import ensure_state_structure, compute_file_checksum, load_project_state, save_project_state, register_artifact

@pytest.fixture(autouse=True)
def reset_state():
    """Reset state before each test to ensure isolation."""
    clear_unresolved_log()
    yield
    clear_unresolved_log()

class TestUnresolvedLogging:
    def test_unresolved_log(self, tmp_path, monkeypatch):
        """
        Test T011: Verify that unresolved realizations are logged to
        data/raw/metadata.json and state/unresolved_realizations.json.
        """
        # Setup temp paths for testing
        data_raw = tmp_path / "data" / "raw"
        state_dir = tmp_path / "state"
        data_raw.mkdir(parents=True)
        state_dir.mkdir(parents=True)

        # Monkeypatch the module constants
        monkeypatch.setattr("state_manager.DATA_RAW_DIR", data_raw)
        monkeypatch.setattr("state_manager.STATE_DIR", state_dir)
        monkeypatch.setattr("state_manager.METADATA_FILE", data_raw / "metadata.json")
        monkeypatch.setattr("state_manager.UNRESOLVED_LOG_FILE", state_dir / "unresolved_realizations.json")

        # Log a single unresolved realization
        delta = 0.2
        rid = 42
        reason = "TEBD convergence failure"
        details = {"iterations": 50, "final_energy": -0.5}

        log_unresolved_realization(delta, rid, reason, details)

        # Verify metadata.json exists and contains summary
        assert METADATA_FILE.exists(), "metadata.json was not created"
        metadata = _load_metadata()

        assert metadata["unresolved_summary"]["total_count"] == 1
        assert str(delta) in metadata["unresolved_summary"]["by_delta"]
        assert metadata["unresolved_summary"]["by_delta"][str(delta)] == 1
        assert reason in metadata["unresolved_summary"]["by_reason"]
        assert metadata["unresolved_summary"]["by_reason"][reason] == 1

        # Verify unresolved_realizations.json exists and contains details
        assert UNRESOLVED_LOG_FILE.exists(), "unresolved_realizations.json was not created"
        log_entries = _load_unresolved_log()
        assert len(log_entries) == 1
        entry = log_entries[0]
        assert entry["delta"] == delta
        assert entry["realization_id"] == rid
        assert entry["reason"] == reason
        assert entry["details"] == details

    def test_batch_logging(self, tmp_path, monkeypatch):
        """Test batch logging of unresolved realizations."""
        data_raw = tmp_path / "data" / "raw"
        state_dir = tmp_path / "state"
        data_raw.mkdir(parents=True)
        state_dir.mkdir(parents=True)

        monkeypatch.setattr("state_manager.DATA_RAW_DIR", data_raw)
        monkeypatch.setattr("state_manager.STATE_DIR", state_dir)
        monkeypatch.setattr("state_manager.METADATA_FILE", data_raw / "metadata.json")
        monkeypatch.setattr("state_manager.UNRESOLVED_LOG_FILE", state_dir / "unresolved_realizations.json")

        rids = [1, 2, 3]
        log_unresolved_batch(0.5, rids, "Numerical overflow")

        summary = get_unresolved_summary()
        assert summary["total_count"] == 3
        assert summary["by_delta"]["0.5000"] == 3
        assert summary["by_reason"]["Numerical overflow"] == 3

    def test_filtering(self, tmp_path, monkeypatch):
        """Test filtering by delta and reason."""
        data_raw = tmp_path / "data" / "raw"
        state_dir = tmp_path / "state"
        data_raw.mkdir(parents=True)
        state_dir.mkdir(parents=True)

        monkeypatch.setattr("state_manager.DATA_RAW_DIR", data_raw)
        monkeypatch.setattr("state_manager.STATE_DIR", state_dir)
        monkeypatch.setattr("state_manager.METADATA_FILE", data_raw / "metadata.json")
        monkeypatch.setattr("state_manager.UNRESOLVED_LOG_FILE", state_dir / "unresolved_realizations.json")

        log_unresolved_realization(0.2, 1, "Error A")
        log_unresolved_realization(0.2, 2, "Error B")
        log_unresolved_realization(0.5, 3, "Error A")

        # Filter by delta
        by_delta = get_unresolved_by_delta(0.2)
        assert len(by_delta) == 2

        # Filter by reason
        by_reason = get_unresolved_by_reason("Error A")
        assert len(by_reason) == 2

class TestStateConfiguration:
    def test_state_structure_creation(self, tmp_path, monkeypatch):
        """Test T012: Ensure state directory structure is created."""
        state_dir = tmp_path / "state"
        monkeypatch.setattr("state_utils.STATE_DIR", state_dir)

        # This should create the directory structure
        ensure_state_structure()

        assert state_dir.exists()
        assert (state_dir / "projects").exists()

    def test_checksums(self, tmp_path, monkeypatch):
        """Test T012: Verify checksum computation and state saving."""
        state_dir = tmp_path / "state"
        projects_dir = state_dir / "projects"
        projects_dir.mkdir(parents=True)

        monkeypatch.setattr("state_utils.STATE_DIR", state_dir)
        monkeypatch.setattr("state_utils.PROJECTS_DIR", projects_dir)

        # Create a dummy artifact
        artifact_path = projects_dir / "test_artifact.txt"
        artifact_path.write_text("test content")

        checksum = compute_file_checksum(artifact_path)
        assert checksum is not None
        assert len(checksum) == 64  # SHA256 hex length

        # Save project state
        project_state = {
            "project_id": "PROJ-308-test",
            "artifacts": {
                "test_artifact.txt": checksum
            }
        }
        save_project_state(project_state)

        # Load and verify
        loaded_state = load_project_state()
        assert loaded_state["project_id"] == "PROJ-308-test"
        assert "test_artifact.txt" in loaded_state["artifacts"]
        assert loaded_state["artifacts"]["test_artifact.txt"] == checksum
