"""Tests for the DAGExecutor implementation."""

import json
from pathlib import Path

import pytest

from code.main_pipeline import DAGExecutor, DependencyValidationError


@pytest.fixture
def simple_dag(tmp_path: Path) -> Path:
    """Create a minimal DAG YAML file for testing."""
    dag_content = {
        "task_a": [],
        "task_b": ["task_a"],
        "task_c": ["task_b"],
    }
    dag_path = tmp_path / "pipeline_dag.yaml"
    dag_path.write_text(json.dumps(dag_content))
    return dag_path


def test_executor_loads_and_validates(simple_dag: Path):
    """The executor should load the DAG without errors."""
    executor = DAGExecutor(simple_dag)
    assert executor.dag == {
        "task_a": [],
        "task_b": ["task_a"],
        "task_c": ["task_b"],
    }
    # No exception means acyclic validation passed


def test_run_task_respects_dependencies(simple_dag: Path):
    executor = DAGExecutor(simple_dag)

    order = []

    def a():
        order.append("a")

    def b():
        order.append("b")

    def c():
        order.append("c")

    # Running out of order must raise
    with pytest.raises(DependencyValidationError):
        executor.run_task("task_b", b)

    # Correct order works
    executor.run_task("task_a", a)
    executor.run_task("task_b", b)
    executor.run_task("task_c", c)

    assert order == ["a", "b", "c"]


def test_execute_all_runs_in_topological_order(simple_dag: Path):
    executor = DAGExecutor(simple_dag)

    order = []

    def make_task(name):
        def _task():
            order.append(name)

        return _task

    task_funcs = {
        "task_a": make_task("a"),
        "task_b": make_task("b"),
        "task_c": make_task("c"),
    }

    executor.execute_all(task_funcs)

    assert order == ["a", "b", "c"]


def test_execute_all_detects_missing_callable(simple_dag: Path):
    executor = DAGExecutor(simple_dag)
    task_funcs = {"task_a": lambda: None, "task_b": lambda: None}  # missing task_c
    with pytest.raises(KeyError):
        executor.execute_all(task_funcs)


def test_cycle_detection(tmp_path: Path):
    """A DAG containing a cycle must raise during initialisation."""
    cyclic = {
        "a": ["c"],
        "b": ["a"],
        "c": ["b"],
    }
    dag_path = tmp_path / "cyclic.yaml"
    dag_path.write_text(json.dumps(cyclic))
    with pytest.raises(ValueError, match="Cycle detected"):
        DAGExecutor(dag_path)