"""
Unit tests for the TaskRunner module.
"""
import os
import tempfile
import yaml
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the class under test
from src.tasks.task_runner import TaskRunner


class TestTaskRunner:
    """Tests for the TaskRunner class."""

    @pytest.fixture
    def temp_task_file(self, tmp_path):
        """Create a temporary task definitions file."""
        task_def_path = tmp_path / "task_definitions.yaml"
        tasks = {
            "T001": {
                "task_id": "T001",
                "modalities": ["time_series"],
                "datasets": ["UCI_HAR"],
                "label_column": "activity"
            },
            "T002": {
                "task_id": "T002",
                "modalities": ["tabular", "text"],
                "datasets": ["DROP", "MUST"],
                "label_column": "answer"
            },
            "T003_INVALID": {
                "task_id": "T003_INVALID",
                # Missing required fields
            }
        }
        with open(task_def_path, 'w') as f:
            yaml.dump(tasks, f)
        return task_def_path

    @pytest.fixture
    def temp_state_file(self, tmp_path):
        """Create a temporary state file."""
        state_path = tmp_path / "state.yaml"
        state_data = {
            "artifact_hashes": {},
            "updated_at": "2023-01-01T00:00:00Z"
        }
        with open(state_path, 'w') as f:
            yaml.dump(state_data, f)
        return state_path

    def test_init_loads_tasks(self, temp_task_file, temp_state_file):
        """Test that TaskRunner loads tasks from the file."""
        runner = TaskRunner(
            task_definitions_path=str(temp_task_file),
            state_path=str(temp_state_file)
        )
        assert len(runner.list_tasks()) == 3
        assert "T001" in runner.list_tasks()
        assert "T002" in runner.list_tasks()

    def test_get_task_existing(self, temp_task_file, temp_state_file):
        """Test retrieving an existing task."""
        runner = TaskRunner(
            task_definitions_path=str(temp_task_file),
            state_path=str(temp_state_file)
        )
        task = runner.get_task("T001")
        assert task is not None
        assert task['task_id'] == "T001"
        assert task['modalities'] == ["time_series"]

    def test_get_task_nonexistent(self, temp_task_file, temp_state_file):
        """Test retrieving a non-existent task."""
        runner = TaskRunner(
            task_definitions_path=str(temp_task_file),
            state_path=str(temp_state_file)
        )
        task = runner.get_task("NONEXISTENT")
        assert task is None

    def test_validate_task_valid(self, temp_task_file, temp_state_file):
        """Test validation of a valid task."""
        runner = TaskRunner(
            task_definitions_path=str(temp_task_file),
            state_path=str(temp_state_file)
        )
        assert runner.validate_task("T001") is True
        assert runner.validate_task("T002") is True

    def test_validate_task_invalid_missing_fields(self, temp_task_file, temp_state_file):
        """Test validation of a task missing required fields."""
        runner = TaskRunner(
            task_definitions_path=str(temp_task_file),
            state_path=str(temp_state_file)
        )
        assert runner.validate_task("T003_INVALID") is False

    def test_validate_task_nonexistent(self, temp_task_file, temp_state_file):
        """Test validation of a non-existent task."""
        runner = TaskRunner(
            task_definitions_path=str(temp_task_file),
            state_path=str(temp_state_file)
        )
        assert runner.validate_task("NONEXISTENT") is False

    def test_run_task_success(self, temp_task_file, temp_state_file):
        """Test running a valid task."""
        runner = TaskRunner(
            task_definitions_path=str(temp_task_file),
            state_path=str(temp_state_file)
        )
        result = runner.run_task("T001")
        assert result["task_id"] == "T001"
        assert result["status"] == "completed"
        assert "metrics" in result

    def test_run_task_failure_invalid(self, temp_task_file, temp_state_file):
        """Test running an invalid task raises ValueError."""
        runner = TaskRunner(
            task_definitions_path=str(temp_task_file),
            state_path=str(temp_state_file)
        )
        with pytest.raises(ValueError, match="Validation failed"):
            runner.run_task("T003_INVALID")

    def test_run_task_failure_nonexistent(self, temp_task_file, temp_state_file):
        """Test running a non-existent task raises ValueError."""
        runner = TaskRunner(
            task_definitions_path=str(temp_task_file),
            state_path=str(temp_state_file)
        )
        with pytest.raises(ValueError, match="Validation failed"):
            runner.run_task("NONEXISTENT")
