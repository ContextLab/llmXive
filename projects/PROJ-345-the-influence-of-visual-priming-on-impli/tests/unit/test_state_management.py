"""
Unit tests for state management functionality (T007).
"""
import os
import sys
import tempfile
import yaml
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add code directory to path
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from state_management import (
    init_state_file,
    save_state_file,
    add_artifact_record,
    log_execution,
    get_project_state_dir,
    get_state_root
)


class TestStateManagement:
    """Tests for state management functions."""

    @pytest.fixture
    def temp_state_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @patch('state_management.get_path')
    def test_init_state_file_creates_new(self, mock_get_path, temp_state_dir):
        """Test that init_state_file creates a new state.yaml when it doesn't exist."""
        project_id = "TEST-PROJECT"
        mock_get_path.return_value = temp_state_dir

        state = init_state_file(project_id)

        # Verify state structure
        assert state["project_id"] == project_id
        assert "initialized_at" in state
        assert state["version"] == "1.0.0"
        assert "principle_v" in state
        assert state["principle_v"]["status"] == "initialized"

        # Verify file was created
        state_file = get_project_state_dir(project_id) / "state.yaml"
        assert state_file.exists()

    @patch('state_management.get_path')
    def test_init_state_file_loads_existing(self, mock_get_path, temp_state_dir):
        """Test that init_state_file loads existing state.yaml."""
        project_id = "TEST-PROJECT-EXISTING"
        mock_get_path.return_value = temp_state_dir

        # Create a pre-existing state file
        state_dir = get_project_state_dir(project_id)
        state_dir.mkdir(parents=True, exist_ok=True)
        existing_state = {
            "project_id": project_id,
            "initialized_at": "2023-01-01T00:00:00",
            "version": "1.0.0",
            "custom_field": "custom_value"
        }
        with open(state_dir / "state.yaml", 'w') as f:
            yaml.dump(existing_state, f)

        # Load the state
        state = init_state_file(project_id)

        assert state["project_id"] == project_id
        assert state["custom_field"] == "custom_value"
        assert "initialized_at" in state

    @patch('state_management.get_path')
    def test_add_artifact_record(self, mock_get_path, temp_state_dir):
        """Test adding an artifact record to state."""
        project_id = "TEST-PROJECT-ARTIFACT"
        mock_get_path.return_value = temp_state_dir

        init_state_file(project_id)

        add_artifact_record(
            project_id,
            "data/processed/test.csv",
            "data",
            {"rows": 1000, "columns": 5}
        )

        state_file = get_project_state_dir(project_id) / "state.yaml"
        with open(state_file, 'r') as f:
            state = yaml.safe_load(f)

        assert len(state["artifacts"]) == 1
        assert state["artifacts"][0]["name"] == "data/processed/test.csv"
        assert state["artifacts"][0]["type"] == "data"
        assert state["artifacts"][0]["details"]["rows"] == 1000

    @patch('state_management.get_path')
    def test_log_execution(self, mock_get_path, temp_state_dir):
        """Test logging an execution event."""
        project_id = "TEST-PROJECT-LOG"
        mock_get_path.return_value = temp_state_dir

        init_state_file(project_id)

        log_execution(project_id, "T007", "success", "Initialization complete")

        state_file = get_project_state_dir(project_id) / "state.yaml"
        with open(state_file, 'r') as f:
            state = yaml.safe_load(f)

        assert len(state["execution_log"]) == 1
        assert state["execution_log"][0]["task_id"] == "T007"
        assert state["execution_log"][0]["status"] == "success"
        assert "message" in state["execution_log"][0]

    @patch('state_management.get_path')
    def test_get_project_state_dir(self, mock_get_path, temp_state_dir):
        """Test getting the project state directory path."""
        project_id = "TEST-PROJECT-PATH"
        mock_get_path.return_value = temp_state_dir

        path = get_project_state_dir(project_id)

        expected = temp_state_dir / "projects" / project_id
        assert path == expected
        assert path.exists()