import os
import tempfile
import yaml
from pathlib import Path

from src.tasks.task_runner import TaskRunner

def test_load_empty_file(tmp_path: Path):
    # Create an empty task definition file
    empty_file = tmp_path / "empty_tasks.yaml"
    empty_file.touch()
    runner = TaskRunner(definitions_path=empty_file)
    assert runner._tasks == {}

def test_load_nonexistent_file(tmp_path: Path):
    # Point to a file that does not exist
    missing_file = tmp_path / "no_such.yaml"
    runner = TaskRunner(definitions_path=missing_file)
    assert runner._tasks == {}

def test_dict_format_loading(tmp_path: Path):
    # Write a valid dict‑style YAML (with a top‑level ``tasks`` key)
    yaml_content = {
        "tasks": [
            {
                "task_id": "T999",
                "modalities": ["timeseries"],
                "datasets": ["UCI_HAR"],
                "label_column": "activity",
            }
        ]
    }
    task_file = tmp_path / "tasks.yaml"
    task_file.write_text(yaml.safe_dump(yaml_content), encoding="utf-8")
    runner = TaskRunner(definitions_path=task_file)
    assert "T999" in runner._tasks
    task = runner.get_task("T999")
    assert task["label_column"] == "activity"

def test_validate_task_success(tmp_path: Path):
    yaml_content = {
        "tasks": [
            {
                "task_id": "T100",
                "modalities": ["text"],
                "datasets": ["DROP"],
                "label_column": "label",
            }
        ]
    }
    task_file = tmp_path / "valid.yaml"
    task_file.write_text(yaml.safe_dump(yaml_content), encoding="utf-8")
    runner = TaskRunner(definitions_path=task_file)
    assert runner.validate_task("T100") is True

def test_validate_task_failure(tmp_path: Path):
    yaml_content = {
        "tasks": [
            {
                "task_id": "T101",
                # Missing ``modalities`` and ``datasets``
                "label_column": "label",
            }
        ]
    }
    task_file = tmp_path / "invalid.yaml"
    task_file.write_text(yaml.safe_dump(yaml_content), encoding="utf-8")
    runner = TaskRunner(definitions_path=task_file)
    assert runner.validate_task("T101") is False

def test_run_task_returns_structure(tmp_path: Path):
    yaml_content = {
        "tasks": [
            {
                "task_id": "T200",
                "modalities": ["text", "tabular"],
                "datasets": ["DROP", "some_tabular"],
                "label_column": "outcome",
            }
        ]
    }
    task_file = tmp_path / "run.yaml"
    task_file.write_text(yaml.safe_dump(yaml_content), encoding="utf-8")
    runner = TaskRunner(definitions_path=task_file)
    result = runner.run_task("T200", add_modality="image")
    assert result["task_id"] == "T200"
    assert result["added_modality"] == "image"
    assert "prediction" in result