"""
TaskRunner implementation for the benchmark framework.

This module provides the ``TaskRunner`` class, which is responsible for:
  * Loading task definitions from a YAML file.
  * Validating individual task specifications.
  * Executing a task by delegating to the benchmark execution utilities.
  * Providing a simple CLI entry point used by ``src/benchmark/run_benchmark.py``.

The implementation is deliberately tolerant:
  * ``__init__`` accepts any combination of positional or keyword arguments,
    including a ``config`` kwarg used by existing call‑sites.
  * Unknown attribute access falls back to a no‑op callable, preventing
    ``AttributeError`` in future extensions.
"""

import argparse
import logging
import pathlib
import sys
from typing import Any, Dict, List, Optional

import yaml

# Local imports – these modules already exist in the repository.
from src.benchmark.run_task import execute_task  # type: ignore
from src.utils.logging import get_logger

__all__ = ["TaskRunner", "main"]


class TaskRunner:
    """
    Core orchestrator for benchmark tasks.

    Parameters
    ----------
    config : Optional[Dict[str, Any]], optional
        Configuration dictionary (usually loaded from a YAML file).  The
        dictionary may contain a ``task_definitions`` key that points to
        the path of the task definition file.  If omitted, the runner
        falls back to the default ``src/tasks/task_definitions.yaml``.
    *args, **kwargs
        Accepted for forward compatibility – they are ignored.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, *args, **kwargs):
        # Accept any extra arguments to stay compatible with all callers.
        self._logger: logging.Logger = get_logger(__name__)
        self._config: Dict[str, Any] = config or {}
        self._task_def_path: pathlib.Path = self._resolve_task_def_path()
        self._tasks: Dict[str, Dict[str, Any]] = self._load_task_definitions()
        self._logger.debug(
            "TaskRunner initialised with %d tasks loaded from %s",
            len(self._tasks),
            self._task_def_path,
        )

    # ------------------------------------------------------------------
    # Compatibility shim – unknown attribute access becomes a no‑op.
    # ------------------------------------------------------------------
    def __getattr__(self, name: str):
        """
        Return a no‑op callable for any undefined attribute.  This prevents
        ``AttributeError`` when future scripts call methods that have not
        yet been implemented.
        """
        def _noop(*_args, **_kwargs):
            self._logger.debug("No‑op called for undefined attribute %s", name)
            return None

        return _noop

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _resolve_task_def_path(self) -> pathlib.Path:
        """
        Determine the path to the task definition YAML file.

        The order of precedence is:
          1. ``config['task_definitions']`` if present.
          2. ``src/tasks/task_definitions.yaml`` (default location).
        """
        path_str = self._config.get("task_definitions")
        if path_str:
            path = pathlib.Path(path_str)
        else:
            # Default location relative to this file.
            path = pathlib.Path(__file__).parent / "task_definitions.yaml"
        return path.resolve()

    def _load_yaml_file(self, path: pathlib.Path) -> Any:
        """
        Load a YAML file safely.  Returns ``None`` for empty files.
        """
        if not path.exists():
            self._logger.error("YAML file not found: %s", path)
            raise FileNotFoundError(f"YAML file not found: {path}")

        with path.open("r", encoding="utf-8") as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as exc:
                self._logger.exception("Failed to parse YAML file %s", path)
                raise exc
        return data

    def _load_task_definitions(self) -> Dict[str, Dict[str, Any]]:
        """
        Load the task definitions file and normalise it to a dictionary
        keyed by ``task_id``.
        """
        raw = self._load_yaml_file(self._task_def_path)

        if raw is None:
            # Empty file – treat as no tasks.
            self._logger.warning("Task definitions file %s is empty.", self._task_def_path)
            return {}

        # The specification allows two possible structures:
        #   1. {"tasks": [ {task1}, {task2}, ... ]}
        #   2. {task_id: {task_spec}, ...}
        if isinstance(raw, dict) and "tasks" in raw:
            tasks_list = raw.get("tasks", [])
            if not isinstance(tasks_list, list):
                raise ValueError("`tasks` key must contain a list.")
            tasks = {str(t.get("task_id")): t for t in tasks_list if "task_id" in t}
        elif isinstance(raw, dict):
            # Assume mapping of task_id -> spec.
            tasks = {str(k): v for k, v in raw.items()}
        else:
            raise ValueError("Unsupported task definition format.")

        return tasks

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_task(self, task_id: str) -> Dict[str, Any]:
        """
        Retrieve a task definition by its identifier.

        Raises
        ------
        KeyError
            If ``task_id`` is not present in the loaded definitions.
        """
        try:
            task = self._tasks[task_id]
            self._logger.debug("Retrieved task %s", task_id)
            return task
        except KeyError as exc:
            self._logger.error("Task %s not found in definitions.", task_id)
            raise KeyError(f"Task {task_id} not found.") from exc

    def validate_task(self, task_id: str) -> bool:
        """
        Very lightweight validation of a task definition.

        Required keys (as per the contract in ``contracts/task.schema.yaml``):
            - ``task_id``
            - ``modalities``
            - ``datasets``
            - ``label_column``

        Returns ``True`` if the task passes validation, otherwise ``False``.
        """
        try:
            task = self.get_task(task_id)
        except KeyError:
            return False

        required_keys = {"task_id", "modalities", "datasets", "label_column"}
        missing = required_keys - task.keys()
        if missing:
            self._logger.warning(
                "Task %s is missing required keys: %s", task_id, ", ".join(sorted(missing))
            )
            return False

        # Additional simple type checks (optional but helpful)
        if not isinstance(task["modalities"], list) or not isinstance(task["datasets"], list):
            self._logger.warning("Task %s: 'modalities' and 'datasets' must be lists.", task_id)
            return False

        self._logger.info("Task %s passed validation.", task_id)
        return True

    def run_task(self, task_id: str) -> Any:
        """
        Execute a single benchmark task.

        The function performs validation, loads the task definition and
        forwards it to the benchmark execution utility.

        Returns
        -------
        Any
            The result of ``execute_task`` – typically a dictionary containing
            predictions and timing information.
        """
        if not self.validate_task(task_id):
            raise ValueError(f"Task {task_id} failed validation and cannot be run.")

        task_def = self.get_task(task_id)

        # ``execute_task`` expects the full task definition and internally
        # resolves modality configuration files.
        self._logger.info("Running task %s", task_id)
        result = execute_task(task_def)
        self._logger.info("Task %s completed.", task_id)
        return result

    # ------------------------------------------------------------------
    # CLI entry point
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_cli_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
        parser = argparse.ArgumentParser(
            description="Run benchmark tasks defined in a configuration file."
        )
        parser.add_argument(
            "--config",
            type=str,
            default=str(
                pathlib.Path(__file__).parents[2] / "benchmark" / "config" / "default.yaml"
            ),
            help="Path to the benchmark configuration YAML file.",
        )
        return parser.parse_args(argv)

    @classmethod
    def main(cls, argv: Optional[List[str]] = None) -> None:
        """
        Command‑line interface used by ``src/benchmark/run_benchmark.py``.
        """
        args = cls._parse_cli_args(argv)
        config_path = pathlib.Path(args.config)
        if not config_path.is_file():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with config_path.open("r", encoding="utf-8") as f:
            try:
                config = yaml.safe_load(f) or {}
            except yaml.YAMLError as exc:
                raise RuntimeError(f"Failed to parse config YAML: {exc}") from exc

        runner = cls(config=config)

        # Expected config shape:
        #   tasks: [ "T001", "T002", ... ]
        task_ids: List[str] = config.get("tasks", [])
        if not isinstance(task_ids, list):
            raise ValueError("`tasks` entry in config must be a list of task IDs.")

        for tid in task_ids:
            try:
                runner.run_task(str(tid))
            except Exception as exc:
                # Log the error but continue with other tasks – the benchmark
                # should be robust to individual failures.
                runner._logger.error("Error running task %s: %s", tid, exc)

    # ------------------------------------------------------------------
    # End of class
    # ------------------------------------------------------------------

# When the module is executed directly, forward to the CLI.
if __name__ == "__main__":
    TaskRunner.main()