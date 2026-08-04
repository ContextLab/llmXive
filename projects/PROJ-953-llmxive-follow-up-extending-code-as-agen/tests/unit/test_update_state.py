"""
Unit tests for state management functionality.

Tests Constitution Principle V compliance:
- Atomic updates
- Traceable changes
- Auditable history
"""

import os
import yaml
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import pytest

# Mock the STATE_ROOT to use a temporary directory
import code.scripts.update_state as update_state_module

@pytest.fixture
def temp_state_dir():
    """Create a temporary directory for state files."""
    temp_dir = tempfile.mkdtemp()
    original_root = update_state_module.STATE_ROOT
    update_state_module.STATE_ROOT = Path(temp_dir)
    update_state_module.PROJECTS_DIR = Path(temp_dir) / "projects"
    
    yield temp_dir
    
    # Cleanup
    update_state_module.STATE_ROOT = original_root
    update_state_module.PROJECTS_DIR = original_root / "projects"
    shutil.rmtree(temp_dir, ignore_errors=True)

def test_ensure_state_dirs_creates_directory(temp_state_dir):
    """Test that ensure_state_dirs creates the required directory structure."""
    projects_dir = update_state_module.PROJECTS_DIR
    assert not projects_dir.exists()
    
    update_state_module.ensure_state_dirs()
    
    assert projects_dir.exists()
    assert projects_dir.is_dir()

def test_load_state_returns_fresh_structure_when_missing(temp_state_dir):
    """Test loading state for a non-existent project returns fresh structure."""
    project_id = "test-project"
    state = update_state_module.load_state(project_id)
    
    assert "project_id" in state
    assert state["project_id"] == project_id
    assert "created_at" in state
    assert "updated_at" in state
    assert "tasks" in state
    assert "artifacts" in state
    assert "metadata" in state

def test_load_state_preserves_existing_state(temp_state_dir):
    """Test that loading an existing state returns the saved data."""
    project_id = "test-project"
    
    # Create initial state
    update_state_module.update_task_status(project_id, "T001", "completed", {"message": "done"})
    
    # Load again
    state = update_state_module.load_state(project_id)
    
    assert state["project_id"] == project_id
    assert "T001" in state["tasks"]
    assert state["tasks"]["T001"]["current_status"] == "completed"

def test_update_task_status_creates_task_entry(temp_state_dir):
    """Test that updating a task status creates the task entry."""
    project_id = "test-project"
    
    update_state_module.update_task_status(project_id, "T001", "in_progress", {"priority": "high"})
    
    state = update_state_module.load_state(project_id)
    
    assert "T001" in state["tasks"]
    assert state["tasks"]["T001"]["current_status"] == "in_progress"
    assert state["tasks"]["T001"]["priority"] == "high"
    assert len(state["tasks"]["T001"]["history"]) == 1
    assert state["tasks"]["T001"]["history"][0]["status"] == "in_progress"

def test_update_task_status_appends_to_history(temp_state_dir):
    """Test that multiple status updates are recorded in history."""
    project_id = "test-project"
    
    update_state_module.update_task_status(project_id, "T001", "pending")
    update_state_module.update_task_status(project_id, "T001", "in_progress")
    update_state_module.update_task_status(project_id, "T001", "completed")
    
    state = update_state_module.load_state(project_id)
    
    assert len(state["tasks"]["T001"]["history"]) == 3
    assert state["tasks"]["T001"]["history"][0]["status"] == "pending"
    assert state["tasks"]["T001"]["history"][1]["status"] == "in_progress"
    assert state["tasks"]["T001"]["history"][2]["status"] == "completed"
    assert state["tasks"]["T001"]["current_status"] == "completed"

def test_update_task_status_updates_timestamp(temp_state_dir):
    """Test that status updates include timestamps."""
    project_id = "test-project"
    
    update_state_module.update_task_status(project_id, "T001", "completed", {"details": "test"})
    
    state = update_state_module.load_state(project_id)
    
    history_entry = state["tasks"]["T001"]["history"][0]
    assert "timestamp" in history_entry
    assert "details" in history_entry
    assert history_entry["details"]["details"] == "test"

def test_add_artifact_records_artifact(temp_state_dir):
    """Test that adding an artifact records it in state."""
    project_id = "test-project"
    
    update_state_module.add_artifact(
        project_id,
        "T001",
        "code/scripts/test.py",
        "code",
        checksum="abc123",
        metadata={"size": 1024}
    )
    
    state = update_state_module.load_state(project_id)
    
    assert len(state["artifacts"]) == 1
    artifact = state["artifacts"][0]
    assert artifact["task_id"] == "T001"
    assert artifact["path"] == "code/scripts/test.py"
    assert artifact["type"] == "code"
    assert artifact["checksum"] == "abc123"
    assert artifact["metadata"]["size"] == 1024

def test_add_artifact_updates_task_artifacts_list(temp_state_dir):
    """Test that adding an artifact updates the task's artifact list."""
    project_id = "test-project"
    
    update_state_module.add_artifact(project_id, "T001", "code/scripts/test.py", "code")
    
    state = update_state_module.load_state(project_id)
    
    assert "artifacts" in state["tasks"]["T001"]
    assert "code/scripts/test.py" in state["tasks"]["T001"]["artifacts"]

def test_add_artifact_multiple(temp_state_dir):
    """Test adding multiple artifacts to the same task."""
    project_id = "test-project"
    
    update_state_module.add_artifact(project_id, "T001", "code/scripts/test.py", "code")
    update_state_module.add_artifact(project_id, "T001", "tests/test_test.py", "test")
    
    state = update_state_module.load_state(project_id)
    
    assert len(state["artifacts"]) == 2
    assert len(state["tasks"]["T001"]["artifacts"]) == 2

def test_save_state_updates_timestamp(temp_state_dir):
    """Test that saving state updates the timestamp."""
    project_id = "test-project"
    
    state = update_state_module.load_state(project_id)
    first_updated = state["updated_at"]
    
    # Small delay to ensure different timestamp
    import time
    time.sleep(0.01)
    
    update_state_module.save_state(project_id, state)
    
    state = update_state_module.load_state(project_id)
    assert state["updated_at"] >= first_updated

def test_state_persistence_across_loads(temp_state_dir):
    """Test that state persists correctly across multiple load/save cycles."""
    project_id = "test-project"
    
    # Create and update state
    update_state_module.update_task_status(project_id, "T001", "completed")
    update_state_module.add_artifact(project_id, "T001", "code/test.py", "code")
    update_state_module.update_task_status(project_id, "T002", "in_progress")
    
    # Reload state
    state = update_state_module.load_state(project_id)
    
    # Verify all data is present
    assert state["project_id"] == project_id
    assert "T001" in state["tasks"]
    assert "T002" in state["tasks"]
    assert state["tasks"]["T001"]["current_status"] == "completed"
    assert state["tasks"]["T002"]["current_status"] == "in_progress"
    assert len(state["artifacts"]) == 1
    assert state["artifacts"][0]["path"] == "code/test.py"

def test_main_init_command(temp_state_dir, capsys):
    """Test the CLI init command."""
    import sys
    
    # Mock sys.argv
    original_argv = sys.argv
    sys.argv = ["update_state.py", "test-project", "init"]
    
    try:
        update_state_module.main()
    finally:
        sys.argv = original_argv
    
    captured = capsys.readouterr()
    assert "Initialized state" in captured.out
    
    # Verify state file was created
    state_path = update_state_module._get_state_path("test-project")
    assert state_path.exists()

def test_main_status_command(temp_state_dir, capsys):
    """Test the CLI status command."""
    import sys
    
    original_argv = sys.argv
    sys.argv = ["update_state.py", "test-project", "status", "T001", "completed"]
    
    try:
        update_state_module.main()
    finally:
        sys.argv = original_argv
    
    captured = capsys.readouterr()
    assert "Updated task T001 to status: completed" in captured.out
    
    state = update_state_module.load_state("test-project")
    assert state["tasks"]["T001"]["current_status"] == "completed"

def test_main_status_command_with_details(temp_state_dir, capsys):
    """Test the CLI status command with JSON details."""
    import sys
    
    original_argv = sys.argv
    sys.argv = ["update_state.py", "test-project", "status", "T001", "completed", "--details", '{"message": "done"}']
    
    try:
        update_state_module.main()
    finally:
        sys.argv = original_argv
    
    state = update_state_module.load_state("test-project")
    assert state["tasks"]["T001"]["history"][0]["details"]["message"] == "done"

def test_main_artifact_command(temp_state_dir, capsys):
    """Test the CLI artifact command."""
    import sys
    
    original_argv = sys.argv
    sys.argv = ["update_state.py", "test-project", "artifact", "T001", "code/test.py", "code"]
    
    try:
        update_state_module.main()
    finally:
        sys.argv = original_argv
    
    captured = capsys.readouterr()
    assert "Recorded artifact: code/test.py" in captured.out
    
    state = update_state_module.load_state("test-project")
    assert len(state["artifacts"]) == 1
    assert state["artifacts"][0]["path"] == "code/test.py"

def test_main_artifact_command_with_checksum(temp_state_dir, capsys):
    """Test the CLI artifact command with checksum."""
    import sys
    
    original_argv = sys.argv
    sys.argv = ["update_state.py", "test-project", "artifact", "T001", "code/test.py", "code", "--checksum", "abc123"]
    
    try:
        update_state_module.main()
    finally:
        sys.argv = original_argv
    
    state = update_state_module.load_state("test-project")
    assert state["artifacts"][0]["checksum"] == "abc123"

def test_main_unknown_command(temp_state_dir, capsys):
    """Test the CLI with an unknown command."""
    import sys
    
    original_argv = sys.argv
    sys.argv = ["update_state.py", "test-project", "unknown"]
    
    with pytest.raises(SystemExit) as excinfo:
        update_state_module.main()
    
    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "Unknown command" in captured.out