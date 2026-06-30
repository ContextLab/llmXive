"""
Task Runner Module for Heterogeneous Scientific Foundation Model Collaboration Benchmark.

Implements the TaskRunner class to manage, validate, and execute benchmark tasks.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from src.utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)


class TaskRunner:
    """
    Manages benchmark tasks defined in task_definitions.yaml.

    Provides methods to load, validate, retrieve, and execute tasks.
    """

    def __init__(self, task_definitions_path: Optional[Union[str, Path]] = None):
        """
        Initialize the TaskRunner.

        Args:
            task_definitions_path: Path to the task_definitions.yaml file.
                                Defaults to 'src/tasks/task_definitions.yaml' relative to project root.
        """
        self.project_root = Path(__file__).resolve().parent.parent.parent
        if task_definitions_path is None:
            task_definitions_path = self.project_root / "src" / "tasks" / "task_definitions.yaml"
        else:
            task_definitions_path = Path(task_definitions_path)

        self.task_definitions_path = task_definitions_path
        self.tasks: Dict[str, Any] = {}
        self._loaded = False
        self._load_tasks()

        logger.info(f"TaskRunner initialized with definitions from {self.task_definitions_path}")
        logger.info(f"Loaded {len(self.tasks)} tasks")

    def _load_tasks(self) -> None:
        """Load task definitions from the YAML file."""
        if not self.task_definitions_path.exists():
            logger.error(f"Task definitions file not found: {self.task_definitions_path}")
            # Initialize with empty dict to prevent crashes
            self.tasks = {}
            return

        try:
            with open(self.task_definitions_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)

            # Handle both list format and dict format
            if content is None:
                logger.warning("Task definitions file is empty.")
                self.tasks = {}
            elif isinstance(content, list):
                # Convert list of task dicts to dict keyed by task_id
                tasks_dict = {}
                for task in content:
                    if isinstance(task, dict) and 'task_id' in task:
                        tid = str(task['task_id'])
                        tasks_dict[tid] = task
                    else:
                        logger.warning(f"Skipping invalid task entry: {task}")
                self.tasks = tasks_dict
                logger.info(f"Loaded {len(self.tasks)} tasks from list format.")
            elif isinstance(content, dict):
                # Handle dict format where tasks might be under a 'tasks' key
                if 'tasks' in content:
                    tasks_list = content['tasks']
                    if isinstance(tasks_list, list):
                        tasks_dict = {}
                        for task in tasks_list:
                            if isinstance(task, dict) and 'task_id' in task:
                                tid = str(task['task_id'])
                                tasks_dict[tid] = task
                            else:
                                logger.warning(f"Skipping invalid task entry: {task}")
                        self.tasks = tasks_dict
                    else:
                        logger.error("'tasks' key exists but is not a list.")
                        self.tasks = {}
                else:
                    # Assume top-level dict keys are task_ids
                    tasks_dict = {}
                    for key, value in content.items():
                        if isinstance(value, dict):
                            tasks_dict[str(key)] = value
                    self.tasks = tasks_dict
                logger.info(f"Loaded {len(self.tasks)} tasks from dict format.")
            else:
                logger.error(f"Unexpected file format: {type(content)}")
                self.tasks = {}

        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML file: {e}")
            self.tasks = {}
        except Exception as e:
            logger.error(f"Unexpected error loading tasks: {e}")
            self.tasks = {}

    def get_task(self, task_id: Union[str, int, Dict]) -> Optional[Dict[str, Any]]:
        """
        Retrieve a task definition by task_id.

        Args:
            task_id: The unique identifier for the task (string or int).
                     If a dict is passed, it is returned as-is if it looks like a task definition.

        Returns:
            The task definition dictionary if found, None otherwise.
        """
        # Handle case where task_id might be a dict (already a task definition)
        if isinstance(task_id, dict):
            if 'task_id' in task_id:
                return task_id
            logger.warning("Received a dict without 'task_id' key, returning as-is.")
            return task_id

        # Convert to string for consistent lookup
        tid_str = str(task_id)

        if not self._loaded:
            self._load_tasks()

        task = self.tasks.get(tid_str)

        if task is None:
            logger.warning(f"Task '{tid_str}' not found in definitions.")

        return task

    def validate_task(self, task_id: Union[str, int]) -> bool:
        """
        Validate that a task exists and has required fields.

        Required fields (based on spec): task_id, modalities, datasets, label_column (optional but recommended).

        Args:
            task_id: The unique identifier for the task.

        Returns:
            True if the task is valid, False otherwise.
        """
        task = self.get_task(task_id)

        if task is None:
            logger.error(f"Validation failed: Task '{task_id}' not found.")
            return False

        # Check required fields
        required_fields = ['task_id', 'modalities', 'datasets']
        missing_fields = [field for field in required_fields if field not in task]

        if missing_fields:
            logger.error(f"Validation failed for task '{task_id}': Missing required fields: {missing_fields}")
            return False

        # Validate modalities is a list
        if not isinstance(task['modalities'], list):
            logger.error(f"Validation failed for task '{task_id}': 'modalities' must be a list.")
            return False

        # Validate datasets is a list
        if not isinstance(task['datasets'], list):
            logger.error(f"Validation failed for task '{task_id}': 'datasets' must be a list.")
            return False

        logger.info(f"Task '{task_id}' validation passed.")
        return True

    def run_task(self, task_id: Union[str, int]) -> Dict[str, Any]:
        """
        Execute a task.

        Note: This is a placeholder for the actual execution logic which depends on
        model runners, data loaders, and evaluation metrics implemented in other modules.
        This method validates the task and prepares the execution context.

        Args:
            task_id: The unique identifier for the task.

        Returns:
            A dictionary containing the execution result (status, metrics, etc.).
        """
        logger.info(f"Starting execution for task '{task_id}'")

        # Validate task first
        if not self.validate_task(task_id):
            return {
                "status": "failed",
                "task_id": str(task_id),
                "error": "Task validation failed",
                "metrics": {}
            }

        task_def = self.get_task(task_id)

        # Placeholder execution logic
        # In a real implementation, this would:
        # 1. Load datasets specified in task_def['datasets']
        # 2. Route modalities to appropriate models
        # 3. Run inference/prediction
        # 4. Compute metrics
        # 5. Return results

        result = {
            "status": "completed",
            "task_id": str(task_id),
            "task_definition": task_def,
            "metrics": {
                "note": "Full execution logic delegated to model runners and evaluation modules"
            }
        }

        logger.info(f"Task '{task_id}' execution completed with status: {result['status']}")
        return result

    def list_tasks(self) -> List[str]:
        """
        List all available task IDs.

        Returns:
            A list of task IDs (strings).
        """
        if not self._loaded:
            self._load_tasks()
        return list(self.tasks.keys())


def main():
    """
    Main entry point for testing the TaskRunner.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Task Runner CLI")
    parser.add_argument('--task-id', type=str, required=True, help="Task ID to run or validate")
    parser.add_argument('--action', type=str, choices=['run', 'validate', 'get', 'list'], default='get',
                        help="Action to perform")
    parser.add_argument('--definitions', type=str, default=None, help="Path to task definitions file")

    args = parser.parse_args()

    runner = TaskRunner(task_definitions_path=args.definitions)

    if args.action == 'list':
        print(f"Available tasks: {runner.list_tasks()}")
    elif args.action == 'get':
        task = runner.get_task(args.task_id)
        if task:
            print(json.dumps(task, indent=2))
        else:
            print(f"Task {args.task_id} not found")
    elif args.action == 'validate':
        is_valid = runner.validate_task(args.task_id)
        print(f"Task {args.task_id} valid: {is_valid}")
    elif args.action == 'run':
        result = runner.run_task(args.task_id)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()