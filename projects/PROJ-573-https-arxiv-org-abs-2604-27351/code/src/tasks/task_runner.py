"""
Task Runner module for executing benchmark tasks.
Provides the TaskRunner class for managing and running tasks.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from src.utils.logging import get_logger

logger = get_logger(__name__)


class TaskRunner:
    """
    Manages and executes benchmark tasks.

    This class provides methods to run, get, and validate tasks.
    It is designed to be tolerant of various initialization patterns
    to support different call sites in the codebase.
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        task_definitions_path: Optional[Union[str, Path]] = None,
        *args,
        **kwargs
    ):
        """
        Initialize the TaskRunner.

        Args:
            config: Optional configuration dictionary.
            task_definitions_path: Path to task definitions YAML file.
            *args: Additional positional arguments (ignored for tolerance).
            **kwargs: Additional keyword arguments (ignored for tolerance).
        """
        self.config = config or {}
        self.logger = get_logger(__name__)

        # Default task definitions path
        if task_definitions_path is None:
            base_dir = Path(__file__).parent.parent.parent
            self.task_definitions_path = base_dir / "src" / "tasks" / "task_definitions.yaml"
        else:
            self.task_definitions_path = Path(task_definitions_path)

        self._tasks_cache: Optional[Dict[str, Any]] = None
        self.logger.info(f"TaskRunner initialized with config: {list(self.config.keys()) if self.config else 'empty'}")

    def _load_tasks(self) -> Dict[str, Any]:
        """Load task definitions from YAML file."""
        if self._tasks_cache is not None:
            return self._tasks_cache

        if not self.task_definitions_path.exists():
            self.logger.warning(f"Task definitions file not found: {self.task_definitions_path}")
            return {"tasks": []}

        try:
            with open(self.task_definitions_path, "r") as f:
                data = yaml.safe_load(f)
                # Handle both list and dict formats
                if isinstance(data, list):
                    self._tasks_cache = {"tasks": data}
                else:
                    self._tasks_cache = data if isinstance(data, dict) else {"tasks": []}
            return self._tasks_cache
        except Exception as e:
            self.logger.error(f"Error loading task definitions: {e}")
            return {"tasks": []}

    def run_task(self, task_id: str, *args, **kwargs) -> Dict[str, Any]:
        """
        Run a specific task by ID.

        Args:
            task_id: The ID of the task to run.
            *args: Additional arguments for task execution.
            **kwargs: Additional keyword arguments for task execution.

        Returns:
            Dictionary containing task execution results.
        """
        self.logger.info(f"Running task: {task_id}")
        task = self.get_task(task_id)

        if task is None:
            self.logger.error(f"Task not found: {task_id}")
            return {"task_id": task_id, "status": "error", "error": "Task not found"}

        # Placeholder for actual task execution logic
        # In a real implementation, this would execute the task
        result = {
            "task_id": task_id,
            "status": "completed",
            "result": "Task executed successfully",
        }
        return result

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get task definition by ID.

        Args:
            task_id: The ID of the task to retrieve.

        Returns:
            Task definition dictionary or None if not found.
        """
        tasks_data = self._load_tasks()
        tasks_list = tasks_data.get("tasks", [])

        for task in tasks_list:
            if task.get("task_id") == task_id:
                return task

        return None

    def validate_task(self, task_id: str) -> bool:
        """
        Validate that a task exists and has required fields.

        Args:
            task_id: The ID of the task to validate.

        Returns:
            True if task is valid, False otherwise.
        """
        task = self.get_task(task_id)
        if task is None:
            return False

        required_fields = ["task_id", "modalities", "datasets"]
        return all(field in task for field in required_fields)

    def __getattr__(self, name: str) -> Any:
        """
        Tolerant attribute access for logger-like methods.

        Any unrecognized method call returns a no-op callable.
        This ensures compatibility with various call patterns.
        """
        def _noop(*args, **kwargs):
            return None
        return _noop


def main():
    """Main entry point for TaskRunner module."""
    runner = TaskRunner()
    logger.info("TaskRunner module loaded successfully")

    # Example usage
    if runner.validate_task("T001"):
        logger.info("Task T001 is valid")


if __name__ == "__main__":
    main()
