"""
Unit tests for the state management system.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from src.utils.state_manager import (
    _default_state,
    _load_state,
    _save_state,
    _compute_file_checksum,
    _update_artifact_list,
    update_stage_status,
    register_artifact,
    get_state,
    verify_artifact_integrity,
    get_artifact_checksum,
    PROJECT_ID,
    STATE_FILE_PATH
)


@pytest.fixture
def temp_state_dir(tmp_path):
    """Create a temporary directory for state files."""
    # We need to mock the global STATE_DIR to point to tmp_path
    # Since the module imports STATE_DIR at top level, we patch it
    with patch("src.utils.state_manager.STATE_DIR", tmp_path), \
         patch("src.utils.state_manager.STATE_FILE_PATH", tmp_path / f"{PROJECT_ID}.yaml"):
        yield tmp_path


def test_default_state_structure():
    state = _default_state()
    assert state["project_id"] == PROJECT_ID
    assert "last_updated" in state
    assert state["status"] == "initialized"
    assert "artifacts" in state
    assert "stages" in state
    assert all(s in state["stages"] for s in ["ingestion", "preprocessing", "training", "evaluation"])


def test_compute_file_checksum(temp_state_dir):
    test_file = temp_state_dir / "test.txt"
    test_file.write_text("hello world")
    
    checksum = _compute_file_checksum(str(test_file))
    assert len(checksum) == 64  # SHA-256 hex length
    
    # Verify it's consistent
    checksum2 = _compute_file_checksum(str(test_file))
    assert checksum == checksum2


def test_compute_file_checksum_missing_file():
    with pytest.raises(FileNotFoundError):
        _compute_file_checksum("nonexistent_file.txt")


def test_update_artifact_list():
    artifacts = [
        {"path": "data/old.csv", "type": "data", "checksum": "abc"}
    ]
    
    new_artifacts = _update_artifact_list(
        artifacts,
        "data/new.csv",
        "data",
        {"rows": 100}
    )
    
    assert len(new_artifacts) == 2
    paths = [a["path"] for a in new_artifacts]
    assert "data/old.csv" in paths
    assert "data/new.csv" in paths
    assert any(a["path"] == "data/new.csv" and a["metadata"]["rows"] == 100 for a in new_artifacts)


def test_update_artifact_list_replace_existing():
    artifacts = [
        {"path": "data/file.csv", "type": "data", "checksum": "old"}
    ]
    
    new_artifacts = _update_artifact_list(
        artifacts,
        "data/file.csv",
        "data",
        {"rows": 200}
    )
    
    assert len(new_artifacts) == 1
    assert new_artifacts[0]["metadata"]["rows"] == 200


@pytest.mark.parametrize("stage,status", [
    ("ingestion", "completed"),
    ("training", "running"),
    ("preprocessing", "failed")
])
def test_update_stage_status(temp_state_dir, stage, status):
    update_stage_status(stage, status)
    
    state = get_state()
    assert state["stages"][stage]["status"] == status
    assert state["last_updated"] is not None


def test_update_stage_status_creates_new(temp_state_dir):
    update_stage_status("custom_stage", "running")
    
    state = get_state()
    assert "custom_stage" in state["stages"]
    assert state["stages"]["custom_stage"]["status"] == "running"


def test_register_artifact(temp_state_dir):
    # Create a dummy file to register
    dummy_file = temp_state_dir.parent / "dummy.txt"
    dummy_file.write_text("dummy content")
    
    register_artifact("dummy.txt", "test", {"key": "value"})
    
    state = get_state()
    assert len(state["artifacts"]) == 1
    assert state["artifacts"][0]["path"] == "dummy.txt"
    assert state["artifacts"][0]["type"] == "test"
    assert state["artifacts"][0]["metadata"]["key"] == "value"
    assert state["artifacts"][0]["checksum"] is not None  # Should compute checksum if file exists
    
    dummy_file.unlink()


def test_get_state(temp_state_dir):
    state = get_state()
    assert state["project_id"] == PROJECT_ID


def test_verify_artifact_integrity_success(temp_state_dir):
    # Create a file and register it
    test_file = Path("test_integrity.txt")
    test_file.write_text("content")
    
    register_artifact("test_integrity.txt", "test")
    
    # Verify should pass
    assert verify_artifact_integrity("test_integrity.txt") is True
    
    test_file.unlink()


def test_verify_artifact_integrity_fail(temp_state_dir):
    test_file = Path("test_fail.txt")
    test_file.write_text("content")
    
    # Register it
    register_artifact("test_fail.txt", "test")
    
    # Modify the file
    test_file.write_text("modified content")
    
    # Verify should fail
    assert verify_artifact_integrity("test_fail.txt") is False
    
    test_file.unlink()


def test_verify_artifact_missing_file(temp_state_dir):
    assert verify_artifact_integrity("nonexistent.txt") is False


def test_get_artifact_checksum(temp_state_dir):
    test_file = Path("checksum_test.txt")
    test_file.write_text("content")
    
    register_artifact("checksum_test.txt", "test")
    
    checksum = get_artifact_checksum("checksum_test.txt")
    assert checksum is not None
    assert len(checksum) == 64
    
    test_file.unlink()


def test_get_artifact_checksum_not_found(temp_state_dir):
    checksum = get_artifact_checksum("nonexistent.txt")
    assert checksum is None


def test_save_and_load_state(temp_state_dir):
    state = _default_state()
    state["custom_key"] = "custom_value"
    
    _save_state(state)
    
    loaded = _load_state()
    assert loaded["custom_key"] == "custom_value"
    assert loaded["project_id"] == PROJECT_ID