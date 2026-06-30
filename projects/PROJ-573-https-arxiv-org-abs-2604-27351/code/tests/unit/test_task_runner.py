"""
Unit tests for the TaskRunner implementation.

The tests cover:
  * Loading an empty task definition file.
  * Handling a missing file gracefully.
  * Correct parsing of a dictionary‑style YAML definition.
"""

import os
import tempfile
import yaml
import pytest

from src.tasks.task_runner import TaskRunner

@pytest.fixture
def temp_task_file():
    """Create a temporary task definition file."""
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".yaml", delete=False) as tf:
        tf.write(yaml.safe_dump([]))  # start with an empty list
        tf.flush()
        yield tf.name
    os.unlink(tf.name)

def test_load_empty_file(temp_task_file):
    """An empty list should result in an empty task map."""
    runner = TaskRunner(task_definitions_path=temp_task_file)
    assert runner._tasks == {}

def test_load_nonexistent_file():
    """Providing a non‑existent path should raise FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        TaskRunner(task_definitions_path="nonexistent.yaml")

def test_dict_format_loading():
    """The loader must accept a dict keyed by task_id."""
    content = {
        "T001": {"task_id": "T001", "modalities": ["text"], "datasets": ["dummy"], "label_column": "label"},
        "T002": {"task_id": "T002", "modalities": ["tabular"], "datasets": ["dummy2"], "label_column": "outcome"},
    }
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".yaml", delete=False) as tf:
        yaml.safe_dump(content, tf)
        tf.flush()
        path = tf.name

    runner = TaskRunner(task_definitions_path=path)
    assert "T001" in runner._tasks
    assert runner._tasks["T001"]["modalities"] == ["text"]
    assert "T002" in runner._tasks
    os.unlink(path)