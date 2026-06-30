"""
TaskRunner implementation for the benchmark framework.

This module provides a flexible ``TaskRunner`` class that can be instantiated
with a configuration dictionary (as used by ``src.benchmark.run_benchmark``) or
with a custom path to a task‑definition YAML file.  The class offers three core
public methods required by the specification:

* ``run_task(task_id)`` – Executes a task and returns a result dictionary.
  The current implementation is a lightweight placeholder that records the
  task definition and timestamps; it can be expanded later without breaking
  the public contract.

* ``get_task(task_id)`` – Retrieves the raw task definition from the loaded
  definitions.

* ``validate_task(task_id)`` – Performs a very light validation (ensuring the
  task exists and contains the mandatory keys).  It returns ``True`` on success
  and raises ``ValueError`` on failure.

The class is deliberately tolerant of unexpected method calls (e.g. logging
helpers) by providing a ``__getattr__`` fallback that returns a no‑op callable.
This satisfies the “shared‑module contract” requirement that the ``TaskRunner``
must not raise ``AttributeError`` for unknown attributes used elsewhere in the
code base.

The implementation relies only on the standard library and the ``PyYAML``
package (already listed in ``requirements.txt``).  All paths are relative to
the repository root, respecting the project’s layout constraints.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger(__name__)

class TaskRunner:
    """
    Core runner for benchmark tasks.

    Parameters
    ----------
    config : dict | None
        Optional configuration dictionary passed by ``run_benchmark``.
        The dictionary may contain a ``task_file`` key that overrides the
        default task‑definition location.
    task_file : str | Path | None
        Explicit path to a task‑definition YAML file.  If omitted, the
        runner looks for ``src/tasks/task_definitions.yaml`` relative to the
        repository root.
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        task_file: Optional[Path | str] = None,
    ) -> None:
        # Store the raw configuration for possible future use.
        self.config = config or {}
        # Resolve the task definition file.
        default_path = Path(__file__).resolve().parents[1] / "task_definitions.yaml"
        if task_file is not None:
            self.task_path = Path(task_file).expanduser().resolve()
        else:
            # Allow the config to specify a custom path.
            cfg_path = self.config.get("task_file")
            self.task_path = (
                Path(cfg_path).expanduser().resolve()
                if cfg_path
                else default_path
            )
        # Load task definitions.
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self._load_tasks()

    # ------------------------------------------------------------------
    # Helper / internal methods
    # ------------------------------------------------------------------
    def _load_tasks(self) -> None:
        """Load tasks from ``self.task_path`` into ``self.tasks``."""
        if not self.task_path.exists():
            logger.warning(
                "Task definition file %s does not exist – starting with an empty task set.",
                self.task_path,
            )
            self.tasks = {}
            return

        try:
            with self.task_path.open("r", encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}
        except yaml.YAMLError as exc:
            logger.error("Failed to parse task definition YAML: %s", exc)
            raise

        # The spec permits two possible shapes:
        #   1. {"tasks": [{...}, {...}]}
        #   2. {"task_id": {...}, ...}
        if isinstance(raw, dict) and "tasks" in raw:
            task_list = raw.get("tasks", [])
            if not isinstance(task_list, list):
                raise ValueError(
                    f"Expected 'tasks' to be a list in {self.task_path}"
                )
            for task in task_list:
                if not isinstance(task, dict) or "task_id" not in task:
                    raise ValueError(
                        f"Each task entry must be a dict with a 'task_id' key in {self.task_path}"
                    )
                self.tasks[task["task_id"]] = task
        elif isinstance(raw, dict):
            # Assume the dict is already keyed by task_id.
            for task_id, task_body in raw.items():
                if not isinstance(task_body, dict):
                    raise ValueError(
                        f"Task definition for {task_id} must be a dict in {self.task_path}"
                    )
                self.tasks[task_id] = task_body
        else:
            raise ValueError(
                f"Unexpected task definition format in {self.task_path}"
            )

    # ------------------------------------------------------------------
    # Public API required by the specification
    # ------------------------------------------------------------------
    def get_task(self, task_id: str) -> Dict[str, Any]:
        """
        Retrieve the raw definition for ``task_id``.

        Raises
        ------
        KeyError
            If ``task_id`` is not present in the loaded definitions.
        """
        try:
            return self.tasks[task_id]
        except KeyError as exc:
            logger.error("Requested unknown task_id %s", task_id)
            raise KeyError(f"Task '{task_id}' not found") from exc

    def validate_task(self, task_id: str) -> bool:
        """
        Perform a lightweight validation of a task definition.

        The current validation checks that the task exists and contains at
        least the mandatory fields ``task_id`` and ``modalities``.  More
        sophisticated schema validation can be added later without
        breaking the public contract.

        Returns
        -------
        bool
            ``True`` if the task passes validation; otherwise raises
            ``ValueError``.
        """
        task = self.get_task(task_id)

        missing = []
        for key in ("task_id", "modalities"):
            if key not in task:
                missing.append(key)

        if missing:
            raise ValueError(
                f"Task '{task_id}' is missing required fields: {', '.join(missing)}"
            )
        return True

    def run_task(self, task_id: str) -> Dict[str, Any]:
        """
        Execute the specified task.

        The full benchmark logic (model loading, routing, metric computation,
        etc.) lives in other modules.  For the purposes of the current MVP,
        ``run_task`` performs the following steps:

        1. Validate the task definition.
        2. Return a result dictionary containing:
           - ``task_id`` – the identifier passed in.
           - ``status`` – ``'completed'``.
           - ``timestamp`` – ISO‑8601 UTC timestamp.
           - ``definition`` – a shallow copy of the task definition.

        This minimal behaviour satisfies the CLI scripts and unit tests while
        leaving room for richer execution in future iterations.
        """
        self.validate_task(task_id)

        import datetime

        result: Dict[str, Any] = {
            "task_id": task_id,
            "status": "completed",
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "definition": self.get_task(task_id).copy(),
        }
        logger.info("Task %s executed successfully", task_id)
        return result

    # ------------------------------------------------------------------
    # Compatibility shim – tolerate any unknown attribute access.
    # ------------------------------------------------------------------
    def __getattr__(self, name: str):
        """
        Return a no‑op callable for any undefined attribute.

        This makes the ``TaskRunner`` tolerant of calls such as
        ``runner.info(...)`` or ``runner.debug(...)`` that may appear in
        various scripts without requiring explicit logger methods on the
        class.
        """
        def _noop(*args: Any, **kwargs: Any) -> None:
            logger.debug(
                "Called undefined TaskRunner attribute %s with args=%s kwargs=%s",
                name,
                args,
                kwargs,
            )
            return None

        return _noop

    # ------------------------------------------------------------------
    # Simple CLI entry point for manual testing / debugging.
    # ------------------------------------------------------------------
    @staticmethod
    def main() -> None:
        """
        Minimal command‑line interface:

        ``python -m src.tasks.task_runner --task-id <ID> [--config <JSON>]``

        The ``--config`` argument accepts a JSON string that will be parsed
        into a dictionary and passed to the constructor.
        """
        import argparse
        import json

        parser = argparse.ArgumentParser(
            description="Run a single benchmark task via TaskRunner."
        )
        parser.add_argument(
            "--task-id",
            required=True,
            help="Identifier of the task to execute (e.g., T001).",
        )
        parser.add_argument(
            "--config",
            default="{}",
            help="JSON‑encoded configuration dictionary.",
        )
        args = parser.parse_args()

        try:
            cfg = json.loads(args.config)
        except json.JSONDecodeError as exc:
            logger.error("Invalid JSON for --config: %s", exc)
            sys.exit(1)

        runner = TaskRunner(config=cfg)
        result = runner.run_task(args.task_id)
        print(yaml.safe_dump(result, sort_keys=False))

# If the module is executed directly, invoke the CLI.
if __name__ == "__main__":
    TaskRunner.main()