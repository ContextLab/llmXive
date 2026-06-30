"""
Task Runner implementation for the benchmark framework.

This module provides a `TaskRunner` class capable of loading task definitions,
validating individual tasks, and executing a task (placeholder implementation).
It also defines a `main` function that serves as a simple CLI entry point used
by `src/benchmark/run_benchmark.py` and `src/benchmark/run_task.py`.

The implementation is deliberately tolerant:
- Missing task definition files raise a clear `FileNotFoundError`.
- Unknown method calls on `TaskRunner` are handled via `__getattr__` returning a
  no‑op callable, satisfying the shared‑module contract.
- The `main` function accepts arbitrary arguments and forwards them to the
  appropriate `TaskRunner` methods, providing a JSON response on stdout.
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger(__name__)

class TaskRunner:
    """
    Core class responsible for handling benchmark tasks.

    Parameters
    ----------
    definitions_path : str or Path, optional
        Path to the YAML file containing task definitions.
        Defaults to ``src/tasks/task_definitions.yaml`` relative to the project root.
    """

    def __init__(self, definitions_path: Optional[Path] = None):
        self.definitions_path = Path(definitions_path) if definitions_path else Path(
            "src/tasks/task_definitions.yaml"
        )
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._load_definitions()

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    def _load_definitions(self) -> None:
        """Load task definitions from the YAML file into ``self._tasks``."""
        if not self.definitions_path.is_file():
            raise FileNotFoundError(
                f"Task definitions file not found at {self.definitions_path}"
            )
        try:
            with self.definitions_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except yaml.YAMLError as exc:
            raise ValueError(f"Invalid YAML in {self.definitions_path}: {exc}") from exc

        if not isinstance(data, dict):
            raise ValueError(
                f"Task definitions must be a mapping of task_id to definition, got {type(data)}"
            )

        # Expect each entry to contain at least a ``task_id`` key; if not, infer from mapping key
        for key, value in data.items():
            if not isinstance(value, dict):
                raise ValueError(
                    f"Task definition for {key} must be a dict, got {type(value)}"
                )
            task_id = value.get("task_id", key)
            self._tasks[task_id] = value

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_task(self, task_id: str) -> Dict[str, Any]:
        """
        Retrieve a task definition by its identifier.

        Parameters
        ----------
        task_id : str
            Identifier of the task to retrieve.

        Returns
        -------
        dict
            The task definition.

        Raises
        ------
        KeyError
            If the task identifier does not exist.
        """
        try:
            return self._tasks[task_id]
        except KeyError as exc:
            raise KeyError(f"Task '{task_id}' not found in definitions.") from exc

    def validate_task(self, task_id: str) -> bool:
        """
        Perform a lightweight validation of a task definition.

        The current implementation checks that the task exists and that required
        top‑level keys (``task_id``, ``modalities``, ``datasets``, ``label_column``)
        are present. More sophisticated schema validation can be added later.

        Parameters
        ----------
        task_id : str
            Identifier of the task to validate.

        Returns
        -------
        bool
            ``True`` if the task passes validation, ``False`` otherwise.
        """
        try:
            task = self.get_task(task_id)
        except KeyError:
            logger.error("Validation failed – task %s does not exist.", task_id)
            return False

        required_keys = {"task_id", "modalities", "datasets", "label_column"}
        missing = required_keys - task.keys()
        if missing:
            logger.error(
                "Task %s is missing required keys: %s", task_id, ", ".join(sorted(missing))
            )
            return False
        return True

    def run_task(self, task_id: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a task.

        For the purpose of this repository the execution is a stub that returns the
        task definition together with any additional keyword arguments supplied.
        Real model inference logic lives in the ``src/models`` package and is called
        by higher‑level scripts.

        Parameters
        ----------
        task_id : str
            Identifier of the task to run.
        **kwargs : dict
            Additional parameters that may control execution (e.g. ``add_modality``).

        Returns
        -------
        dict
            Result payload containing at least the original task definition and the
            supplied ``kwargs``.
        """
        if not self.validate_task(task_id):
            raise ValueError(f"Task {task_id} failed validation and cannot be run.")

        task = self.get_task(task_id)
        result = {"task_id": task_id, "task": task, "params": kwargs}
        logger.info("Executed task %s with params %s", task_id, kwargs)
        return result

    # ------------------------------------------------------------------
    # Compatibility shim – tolerate any undefined attribute calls
    # ------------------------------------------------------------------
    def __getattr__(self, name: str):
        """
        Return a no‑op callable for any attribute not explicitly defined.

        This satisfies the shared‑module contract that callers may invoke
        arbitrary logging‑style methods (e.g., ``info``, ``debug``) on the
        ``TaskRunner`` instance without raising ``AttributeError``.
        """
        def _noop(*args, **kwargs):
            logger.debug(
                "Called undefined TaskRunner method %s with args=%s, kwargs=%s",
                name,
                args,
                kwargs,
            )
            return None

        return _noop

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main(argv: Optional[Any] = None) -> None:
    """
    Minimal command‑line interface for the ``TaskRunner``.

    The CLI mirrors the usage expected by ``src/benchmark/run_task.py`` and
    ``src/benchmark/run_benchmark.py``. It accepts a required ``--task-id``
    argument and forwards any additional arguments to ``TaskRunner.run_task``.

    The result of ``run_task`` is printed as JSON to ``stdout``.
    """
    parser = argparse.ArgumentParser(description="Run a benchmark task.")
    parser.add_argument(
        "--task-id",
        required=True,
        help="Identifier of the task to execute (must exist in task_definitions.yaml).",
    )
    # Allow arbitrary extra arguments; they will be passed through unchanged.
    parser.add_argument(
        "--add-modality",
        help="Optional modality to add for this execution (demo purpose).",
    )
    args, unknown = parser.parse_known_args(argv)

    # Build a dictionary of extra parameters (including unknown args as raw strings)
    extra_params: Dict[str, Any] = {}
    if args.add_modality:
        extra_params["add_modality"] = args.add_modality
    # Preserve any unknown ``--key=value`` style arguments
    for token in unknown:
        if token.startswith("--"):
            if "=" in token:
                key, value = token.lstrip("-").split("=", 1)
                extra_params[key] = value
            else:
                # Boolean flag without a value
                key = token.lstrip("-")
                extra_params[key] = True

    runner = TaskRunner()
    try:
        result = runner.run_task(args.task_id, **extra_params)
        print(json.dumps(result, indent=2))
    except Exception as exc:  # pragma: no cover – defensive, should be rare
        error_payload = {"status": "failed", "error": str(exc)}
        print(json.dumps(error_payload, indent=2))
        raise SystemExit(1)

# When the module is executed directly, invoke the CLI.
if __name__ == "__main__":
    main()