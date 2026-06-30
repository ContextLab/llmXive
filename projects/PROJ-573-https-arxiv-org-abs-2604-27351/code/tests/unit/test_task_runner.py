"""
Unit tests for the TaskRunner module.
"""
import os
import tempfile
import yaml
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.tasks.task_runner import TaskRunner


@pytest.fixture
def temp_task_file():
    """Create a temporary task definitions file."""
    tasks = [
        {
            "task_id": "T001",
            "modalities": ["timeseries", "tabular"],
            "datasets": ["UCI_HAR"],
            "label_column": "activity"
        },
        {
            "task_id": "T002",
            "modalities": ["text"],
            "datasets": ["DROP"],
            "label_column": "answer"
        }
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(tasks, f)
        temp_path = f.name
    
    yield temp_path
    
    os.unlink(temp_path)


@pytest.fixture
def runner_with_tasks(temp_task_file):
    """Create a TaskRunner with the temporary task file."""
    return TaskRunner(task_definitions_path=temp_task_file)


class TestTaskRunner:
    """Tests for the TaskRunner class."""
    
    def test_init_with_valid_path(self, temp_task_file):
        """Test initialization with a valid file path."""
        runner = TaskRunner(task_definitions_path=temp_task_file)
        assert runner.task_definitions_path == Path(temp_task_file)
        assert "T001" in runner.tasks
        assert "T002" in runner.tasks
    
    def test_init_with_default_path_missing(self):
        """Test initialization when default path does not exist."""
        # Create a runner pointing to a non-existent default location
        # We need to mock the default path resolution or use a specific path
        # Here we test the behavior when the file doesn't exist by passing a non-existent path
        with tempfile.TemporaryDirectory() as tmpdir:
            non_existent = os.path.join(tmpdir, "non_existent.yaml")
            runner = TaskRunner(task_definitions_path=non_existent)
            assert runner.tasks == {}
    
    def test_get_task_found(self, runner_with_tasks):
        """Test retrieving an existing task."""
        task = runner_with_tasks.get_task("T001")
        assert task is not None
        assert task["task_id"] == "T001"
        assert task["modalities"] == ["timeseries", "tabular"]
    
    def test_get_task_not_found(self, runner_with_tasks):
        """Test retrieving a non-existent task."""
        task = runner_with_tasks.get_task("T999")
        assert task is None
    
    def test_validate_task_valid(self, runner_with_tasks):
        """Test validation of a valid task."""
        is_valid, errors = runner_with_tasks.validate_task("T001")
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_task_not_found(self, runner_with_tasks):
        """Test validation of a non-existent task."""
        is_valid, errors = runner_with_tasks.validate_task("T999")
        assert is_valid is False
        assert "Task definition not found for ID: T999" in errors
    
    def test_validate_task_missing_field(self, temp_task_file):
        """Test validation of a task missing required fields."""
        tasks = [
            {
                "task_id": "T003",
                "modalities": ["text"]
                # Missing label_column
            }
        ]
        
        with open(temp_task_file, 'w') as f:
            yaml.dump(tasks, f)
        
        runner = TaskRunner(task_definitions_path=temp_task_file)
        is_valid, errors = runner.validate_task("T003")
        
        assert is_valid is False
        assert any("Missing required field: label_column" in e for e in errors)
    
    def test_run_task_success(self, runner_with_tasks):
        """Test running a valid task."""
        result = runner_with_tasks.run_task("T001")
        
        assert result["task_id"] == "T001"
        assert result["status"] == "completed"
        assert "execution_time" in result
        assert result["details"]["modalities"] == ["timeseries", "tabular"]
    
    def test_run_task_invalid(self, runner_with_tasks):
        """Test running a non-existent task raises error."""
        with pytest.raises(ValueError) as exc_info:
            runner_with_tasks.run_task("T999")
        
        assert "Task validation failed" in str(exc_info.value)
    
    def test_list_tasks(self, runner_with_tasks):
        """Test listing all tasks."""
        task_ids = runner_with_tasks.list_tasks()
        assert set(task_ids) == {"T001", "T002"}


def test_load_empty_file():
    """Test loading an empty YAML file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("")
        temp_path = f.name
    
    try:
        runner = TaskRunner(task_definitions_path=temp_path)
        assert runner.tasks == {}
    finally:
        os.unlink(temp_path)


def test_load_nonexistent_file():
    """Test loading a non-existent file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        non_existent = os.path.join(tmpdir, "does_not_exist.yaml")
        runner = TaskRunner(task_definitions_path=non_existent)
        assert runner.tasks == {}


def test_dict_format_loading():
    """Test loading tasks in dictionary format."""
    tasks = {
        "T001": {
            "modalities": ["timeseries"],
            "label_column": "activity"
        },
        "T002": {
            "modalities": ["text"],
            "label_column": "answer"
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(tasks, f)
        temp_path = f.name
    
    try:
        runner = TaskRunner(task_definitions_path=temp_path)
        assert len(runner.tasks) == 2
        assert "T001" in runner.tasks
        assert "T002" in runner.tasks
    finally:
        os.unlink(temp_path)