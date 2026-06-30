import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union

logger = logging.getLogger(__name__)


class TaskRunner:
    """
    Simple utility to load, validate and (placeholder) run task definitions.

    The task definitions are stored in ``src/tasks/task_definitions.yaml`` and
    follow the schema described in ``contracts/task.schema.yaml``.  Each task
    must contain at least the keys ``task_id``, ``modalities``, ``datasets``,
    and ``label_column``.
    """

    def __init__(self, definitions_path: Optional[Union[str, Path]] = None):
        """
        Initialise the runner and load the task definitions.

        Parameters
        ----------
        definitions_path: Optional[Union[str, Path]]
            Path to the YAML file containing task definitions.  If omitted
            the default location ``src/tasks/task_definitions.yaml`` (relative
            to this file) is used.
        """
        if definitions_path is None:
            self.definitions_path = Path(__file__).with_name("task_definitions.yaml")
        else:
            self.definitions_path = Path(definitions_path)

        self.tasks = self._load_definitions()

    def _load_definitions(self) -> Dict[str, Dict[str, Any]]:
        """
        Load the YAML file and return a mapping of ``task_id`` → task dict.
        Supports both a list of tasks or a mapping already.
        """
        if not self.definitions_path.is_file():
            logger.error("Task definitions file not found: %s", self.definitions_path)
            raise FileNotFoundError(f"Task definitions file not found: {self.definitions_path}")

        with self.definitions_path.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}

        tasks: Dict[str, Dict[str, Any]] = {}
        if isinstance(raw, list):
            for task in raw:
                tid = task.get("task_id")
                if tid:
                    tasks[tid] = task
        elif isinstance(raw, dict):
            tasks = raw
        else:
            logger.error("Unexpected format in task definitions YAML")
            raise ValueError("Unexpected format in task definitions YAML")

        return tasks

    @staticmethod
    def _normalize_task_id(task_id: Union[str, int]) -> str:
        """
        Normalise a task identifier to the canonical string form ``T###``.
        """
        if isinstance(task_id, int):
            return f"T{task_id:03d}"
        return str(task_id)

    def get_task(self, task_id: Union[str, int]) -> Dict[str, Any]:
        """
        Retrieve the raw task definition dictionary.

        Raises
        ------
        KeyError
            If the task identifier does not exist in the loaded definitions.
        """
        tid = self._normalize_task_id(task_id)
        task = self.tasks.get(tid)
        if task is None:
            raise KeyError(f"Task definition not found for ID: {task_id}")
        return task

    def validate_task(self, task_id: Union[str, int]) -> bool:
        """
        Validate that a task contains the required fields.

        Returns ``True`` if the task is valid, otherwise ``False``.
        """
        task = self.get_task(task_id)
        required = {"task_id", "modalities", "datasets", "label_column"}
        missing = required - task.keys()
        if missing:
            logger.warning(
                "Task %s is missing required fields: %s", task_id, ", ".join(sorted(missing))
            )
            return False
        return True

    def run_task(self, task_id: Union[str, int]) -> Dict[str, Any]:
        """
        Placeholder implementation that validates and then returns the task
        definition.  Real execution logic (model routing, inference, etc.) is
        implemented elsewhere; this method provides a stable entry point for
        the CLI and for unit tests.

        Raises
        ------
        ValueError
            If validation fails.
        """
        if not self.validate_task(task_id):
            raise ValueError(f"Task {task_id} failed validation")

        task = self.get_task(task_id)
        logger.info("Running task %s", task_id)
        # In a full implementation this would trigger the model routing,
        # data loading, inference, etc.  For now we simply return the task
        # definition so that downstream code can inspect it.
        return task


def main() -> None:
    """
    Simple command‑line interface for the TaskRunner.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Run a benchmark task")
    parser.add_argument("task_id", help="Identifier of the task to run (e.g. T001 or 1)")
    args = parser.parse_args()

    runner = TaskRunner()
    try:
        result = runner.run_task(args.task_id)
        print(result)
    except Exception as exc:  # pragma: no cover – CLI error handling
        logger.error("Failed to run task %s: %s", args.task_id, exc)
        raise


if __name__ == "__main__":
    main()
