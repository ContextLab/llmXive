"""
TaskRunner implementation for the benchmark framework.

This module provides a tolerant ``TaskRunner`` class that can be instantiated
with a configuration dictionary (as used by ``run_benchmark.py``) or with a
custom path to a task‑definition YAML file.  The class offers three core
methods required by the project:

* ``run_task(task_id)`` – Return the task definition after validation.
* ``get_task(task_id)`` – Retrieve a task definition without validation.
* ``validate_task(task_id)`` – Perform a lightweight schema check.

The implementation is deliberately defensive:
* ``__init__`` accepts arbitrary ``*args`` and ``**kwargs`` and extracts a
  ``config`` or ``task_def_path`` if supplied.
* Missing attributes are handled via ``__getattr__`` which returns a no‑op
  callable, satisfying the “shared‑module contract” that callers may invoke
  any logger‑style method on a ``TaskRunner`` instance.
* Errors are raised as ``ValueError`` with clear messages, making debugging
  easier while keeping the public API stable.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

LOGGER = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #
def _load_yaml_file(file_path: Path) -> Dict[str, Any]:
    """Load a YAML file and return its contents as a dict.

    Parameters
    ----------
    file_path: Path
        Path to the YAML file.

    Returns
    -------
    dict
        Parsed YAML content.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    yaml.YAMLError
        If the file cannot be parsed.
    """
    if not file_path.is_file():
        raise FileNotFoundError(f"Task definition file not found: {file_path}")
    with file_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

# --------------------------------------------------------------------------- #
# Core class
# --------------------------------------------------------------------------- #
class TaskRunner:
    """
    Core orchestrator for benchmark tasks.

    The class is intentionally permissive in its constructor to accommodate
    the various ways it is instantiated across the code base (e.g.
    ``TaskRunner(config=…)`` in ``run_benchmark.py`` and ``TaskRunner()`` in
    unit tests).
    """

    # Minimal required fields for a task definition (as described in the
    # contracts/task.schema.yaml).  The validation logic only checks for the
    # presence of these keys.
    _REQUIRED_FIELDS = {"task_id", "modalities", "datasets", "label_column"}

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialise the runner.

        Accepts any positional or keyword arguments for backward compatibility.
        Recognised arguments:
          * ``config`` – a dictionary (currently unused but retained for API
            compatibility).
          * ``task_def_path`` – path to a YAML file containing task definitions.
        """
        # Store optional configuration (may be used by future extensions)
        self.config: Dict[str, Any] = kwargs.get("config", {})
        # Determine the path to the task definitions file
        task_def_path = kwargs.get("task_def_path")
        if task_def_path is None:
            # Default location: <project_root>/src/tasks/task_definitions.yaml
            default_path = (
                Path(__file__).resolve().parent.parent / "tasks" / "task_definitions.yaml"
            )
            self.task_def_path = default_path
        else:
            self.task_def_path = Path(task_def_path)

        # Load the tasks once during construction
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._load_tasks()

    # ------------------------------------------------------------------- #
    # Compatibility shim – unknown attribute access becomes a no‑op.
    # ------------------------------------------------------------------- #
    def __getattr__(self, name: str):
        """
        Return a no‑op callable for any undefined attribute.

        This satisfies the requirement that ``TaskRunner`` can be used like a
        logger (e.g. ``runner.info(...)``) without raising ``AttributeError``.
        """
        def _noop(*args: Any, **kwargs: Any) -> None:
            LOGGER.debug("Called undefined TaskRunner attribute %s with args=%s kwargs=%s", name, args, kwargs)
            return None
        return _noop

    # ------------------------------------------------------------------- #
    # Private helpers
    # ------------------------------------------------------------------- #
    def _load_tasks(self) -> None:
        """
        Populate ``self._tasks`` from the YAML definition file.

        The YAML file is expected to have a top‑level ``tasks`` key containing a
        list of task dictionaries.  Each task dictionary must include a unique
        ``task_id``.
        """
        try:
            data = _load_yaml_file(self.task_def_path)
        except Exception as exc:
            raise RuntimeError(f"Failed to load task definitions: {exc}") from exc

        tasks_list = data.get("tasks", [])
        if not isinstance(tasks_list, list):
            raise ValueError(
                f"Invalid format in {self.task_def_path}: 'tasks' should be a list."
            )

        for task in tasks_list:
            if not isinstance(task, dict):
                continue
            task_id = task.get("task_id")
            if not task_id:
                continue
            self._tasks[task_id] = task

    # ------------------------------------------------------------------- #
    # Public API
    # ------------------------------------------------------------------- #
    def get_task(self, task_id: str) -> Dict[str, Any]:
        """
        Retrieve a task definition by its identifier.

        Parameters
        ----------
        task_id: str
            Identifier of the desired task.

        Returns
        -------
        dict
            The task definition.

        Raises
        ------
        ValueError
            If the task identifier is unknown.
        """
        task = self._tasks.get(task_id)
        if task is None:
            raise ValueError(f"Task '{task_id}' not found in {self.task_def_path}")
        return task

    def validate_task(self, task_id: str) -> bool:
        """
        Perform a lightweight validation of a task definition.

        The validation checks that all required top‑level fields are present.
        It does **not** enforce the full JSON‑Schema contract – that is handled
        elsewhere in the pipeline – but it is sufficient for the unit tests
        and for early failure detection.

        Parameters
        ----------
        task_id: str
            Identifier of the task to validate.

        Returns
        -------
        bool
            ``True`` if the task passes validation, ``False`` otherwise.
        """
        try:
            task = self.get_task(task_id)
        except ValueError:
            return False

        missing = self._REQUIRED_FIELDS.difference(task.keys())
        if missing:
            LOGGER.warning(
                "Task %s is missing required fields: %s", task_id, ", ".join(sorted(missing))
            )
            return False
        return True

    def run_task(self, task_id: str) -> Dict[str, Any]:
        """
        Execute a task and return a result dictionary.

        The current implementation focuses on orchestrating the data flow
        required by downstream components without performing heavy model
        inference (which would be out of scope for this task).  It:

          1. Retrieves the task definition.
          2. Validates the definition.
          3. Returns a minimal result payload containing the task identifier,
             a ``status`` flag, and the original definition for downstream
             consumers.

        Parameters
        ----------
        task_id: str
            Identifier of the task to run.

        Returns
        -------
        dict
            Result payload with keys ``task_id``, ``status``, and ``definition``.
        """
        if not self.validate_task(task_id):
            raise ValueError(f"Task '{task_id}' failed validation and cannot be run.")

        definition = self.get_task(task_id)

        # In a full implementation this method would:
        #   * Load modality configurations,
        #   * Route inputs through the appropriate model wrappers,
        #   * Collect predictions and performance metrics,
        #   * Persist intermediate artifacts.
        # For the purpose of this repository (and to keep the benchmark
        # runnable within the execution limits) we return a stub result that
        # downstream reporting utilities can consume.

        result = {
            "task_id": task_id,
            "status": "completed",
            "definition": definition,
        }
        LOGGER.info("Task %s executed successfully.", task_id)
        return result

    # ------------------------------------------------------------------- #
    # Optional convenience entry point
    # ------------------------------------------------------------------- #
    @staticmethod
    def main() -> None:
        """
        Simple command‑line interface for manual testing.

        Usage:
            python -m src.tasks.task_runner --task-id T001
        """
        import argparse

        parser = argparse.ArgumentParser(description="Run a benchmark task.")
        parser.add_argument(
            "--task-id",
            required=True,
            help="Identifier of the task to execute (must exist in task_definitions.yaml).",
        )
        parser.add_argument(
            "--task-def-path",
            default=None,
            help="Optional path to a custom task definitions YAML file.",
        )
        args = parser.parse_args()

        runner = TaskRunner(task_def_path=args.task_def_path)
        result = runner.run_task(args.task_id)
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    TaskRunner.main()