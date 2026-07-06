import json
import os
import tempfile
from pathlib import Path
from unittest import TestCase, mock

import pytest

# We need to mock the environment and paths since we are running tests in isolation
# The state_manager relies on config.env_config and logging_config which assume project structure
# We will mock the _get_state_path to use a temp directory

from code.state_manager import (
    compute_file_checksum,
    load_state,
    save_state,
    register_artifact,
    verify_artifact,
    get_artifact_info,
    list_artifacts,
    record_run,
    get_state_summary,
    ensure_state_directory,
    _get_state_path
)

@pytest.fixture
def temp_state_dir(tmp_path):
    """Create a temporary directory to simulate the project state folder."""
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    return state_dir

@pytest.fixture
def mock_get_state_path(temp_state_dir):
    """Mock _get_state_path to return our temp directory."""
    with mock.patch("code.state_manager._get_state_path", return_value=temp_state_dir / "state.yaml"):
        yield temp_state_dir

def test_compute_file_checksum(mock_get_state_path):
    """Test that checksum computation works correctly."""
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
        f.write("Hello, World!")
        temp_file = f.name

    try:
        checksum = compute_file_checksum(temp_file)
        assert len(checksum) == 64  # SHA-256 hex length
        assert checksum.isalnum()
        
        # Verify determinism
        checksum2 = compute_file_checksum(temp_file)
        assert checksum == checksum2
    finally:
        os.unlink(temp_file)

def test_compute_file_checksum_nonexistent(mock_get_state_path):
    """Test that checksum raises error for missing file."""
    with pytest.raises(FileNotFoundError):
        compute_file_checksum("/nonexistent/path/file.txt")

def test_load_state_empty(mock_get_state_path):
    """Test loading state when file does not exist."""
    state = load_state()
    assert state["version"] == "1.0.0"
    assert state["artifacts"] == {}
    assert state["runs"] == []

def test_register_artifact(mock_get_state_path):
    """Test registering a new artifact."""
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
        f.write("Test data")
        temp_file = f.name

    try:
        # Ensure the state file starts empty
        state_path = mock_get_state_path / "state.yaml"
        if state_path.exists():
            state_path.unlink()

        artifact = register_artifact(temp_file, "test_type", {"key": "value"})
        
        assert artifact["type"] == "test_type"
        assert artifact["path"] == temp_file
        assert "checksum" in artifact
        assert artifact["metadata"]["key"] == "value"

        # Verify it's in the state
        state = load_state()
        found = False
        for key, val in state["artifacts"].items():
            if val["path"] == temp_file:
                found = True
                break
        assert found
    finally:
        os.unlink(temp_file)

def test_verify_artifact_valid(mock_get_state_path):
    """Test verifying an artifact with matching checksum."""
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
        f.write("Verify me")
        temp_file = f.name

    try:
        # Register first
        register_artifact(temp_file, "verify_test")
        
        # Verify should return True
        assert verify_artifact(temp_file, "verify_test") is True
    finally:
        os.unlink(temp_file)

def test_verify_artifact_mismatched(mock_get_state_path):
    """Test verifying an artifact after modification."""
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
        f.write("Original")
        temp_file = f.name

    try:
        # Register original
        register_artifact(temp_file, "modify_test")
        
        # Modify file
        with open(temp_file, 'w') as f:
            f.write("Modified")
        
        # Verify should return False
        assert verify_artifact(temp_file, "modify_test") is False
    finally:
        os.unlink(temp_file)

def test_list_artifacts(mock_get_state_path):
    """Test listing artifacts."""
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as f1:
        f1.write("Data 1")
        temp1 = f1.name
    
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as f2:
        f2.write("Data 2")
        temp2 = f2.name

    try:
        register_artifact(temp1, "type_a")
        register_artifact(temp2, "type_b")
        
        all_artifacts = list_artifacts()
        assert len(all_artifacts) == 2
        
        type_a = list_artifacts("type_a")
        assert len(type_a) == 1
        assert type_a[0]["path"] == temp1
    finally:
        os.unlink(temp1)
        os.unlink(temp2)

def test_record_run(mock_get_state_path):
    """Test recording a run."""
    record_run("test_script.py", ["input1"], ["output1"], "success", 10.5)
    
    state = load_state()
    assert len(state["runs"]) == 1
    run = state["runs"][0]
    assert run["script"] == "test_script.py"
    assert run["status"] == "success"
    assert run["duration_seconds"] == 10.5

def test_get_state_summary(mock_get_state_path):
    """Test getting state summary."""
    summary = get_state_summary()
    assert "total_artifacts" in summary
    assert "total_runs" in summary
    assert "last_updated" in summary
    assert summary["total_artifacts"] == 0
    assert summary["total_runs"] == 0
