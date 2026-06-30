"""
Task Runner Module for Heterogeneous Scientific Foundation Model Collaboration Benchmark.

This module provides the TaskRunner class to manage, validate, and execute tasks
defined in the task_definitions.yaml configuration.

Dependencies:
  - T017: Checksum tracking infrastructure (state/projects/...yaml)
  - T031: Task definitions file (src/tasks/task_definitions.yaml)
  - T011: Task schema contract (contracts/task.schema.yaml)
"""
import os
import yaml
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from src.utils.logging import get_logger
from src.utils.checksum_utils import compute_file_sha256, load_state_file, save_state_file
from src.utils.versioning import update_artifact_timestamp

# Initialize logger
logger = get_logger(__name__)

class TaskRunner:
    """
    Manages task definitions, validation, and execution orchestration.

    The TaskRunner loads task definitions from a YAML file, validates them
    against expected schemas, and provides methods to retrieve or run specific tasks.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the TaskRunner.

        Args:
            config_path: Path to the task_definitions.yaml file.
                        Defaults to src/tasks/task_definitions.yaml relative to project root.
        """
        self.project_root = Path(__file__).resolve().parents[2]
        self.default_config_path = self.project_root / "src" / "tasks" / "task_definitions.yaml"
        self.config_path = Path(config_path) if config_path else self.default_config_path
        
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self._last_loaded_hash: Optional[str] = None

        if not self.config_path.exists():
            logger.warning(f"Task definitions file not found at {self.config_path}. "
                         "Tasks will be empty until file is created.")
            self.tasks = {}
        else:
            self._load_tasks()

    def _load_tasks(self) -> None:
        """Load task definitions from the YAML configuration file."""
        if not self.config_path.exists():
            logger.error(f"Cannot load tasks: file not found at {self.config_path}")
            return

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if data is None:
                self.tasks = {}
                logger.warning("Task definitions file is empty.")
                return

            # Handle both list of tasks and dict of tasks
            if isinstance(data, list):
                for task in data:
                    if 'task_id' in task:
                        self.tasks[task['task_id']] = task
            elif isinstance(data, dict):
                self.tasks = data
            
            # Compute hash for change tracking
            self._last_loaded_hash = compute_file_sha256(str(self.config_path))
            logger.info(f"Loaded {len(self.tasks)} task definitions from {self.config_path}")
            
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse task definitions YAML: {e}")
            self.tasks = {}
        except Exception as e:
            logger.error(f"Unexpected error loading tasks: {e}")
            self.tasks = {}

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a task definition by its ID.

        Args:
            task_id: The unique identifier of the task (e.g., 'T001', 'T023').

        Returns:
            A dictionary containing the task definition, or None if not found.
        """
        return self.tasks.get(task_id)

    def validate_task(self, task_id: str) -> Tuple[bool, List[str]]:
        """
        Validate a task definition against expected schema fields.

        Expected fields based on T031 and contracts/task.schema.yaml:
          - task_id (required)
          - modalities (list)
          - datasets (list)
          - label_column (string)

        Args:
            task_id: The ID of the task to validate.

        Returns:
            A tuple of (is_valid, list_of_errors).
        """
        errors = []
        
        task = self.get_task(task_id)
        if task is None:
            return False, [f"Task ID '{task_id}' not found in definitions."]

        required_fields = ['task_id', 'modalities', 'datasets']
        
        for field in required_fields:
            if field not in task:
                errors.append(f"Missing required field: {field}")
            elif field == 'modalities' or field == 'datasets':
                if not isinstance(task[field], list):
                    errors.append(f"Field '{field}' must be a list")
                elif len(task[field]) == 0:
                    errors.append(f"Field '{field}' cannot be empty")
            elif field == 'task_id' and task[field] != task_id:
                errors.append(f"task_id mismatch: expected '{task_id}', got '{task[field]}'")

        # Optional field validation
        if 'label_column' in task and not isinstance(task['label_column'], str):
            errors.append("Field 'label_column' must be a string")

        return len(errors) == 0, errors

    def run_task(self, task_id: str, custom_args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a task.

        This method orchestrates the execution of a specific task. In the current
        implementation, it performs validation and returns a status report.
        Actual model execution is delegated to the benchmark runner (run_benchmark.py)
        or run_task.py entry points which handle modality-specific routing.

        Args:
            task_id: The ID of the task to run.
            custom_args: Optional dictionary of arguments to override task defaults.

        Returns:
            A dictionary containing execution status and results.
        """
        logger.info(f"Starting execution for task: {task_id}")
        
        # Validate task first
        is_valid, errors = self.validate_task(task_id)
        if not is_valid:
            logger.error(f"Task validation failed for {task_id}: {errors}")
            return {
                "task_id": task_id,
                "status": "failed",
                "error": "Validation failed",
                "details": errors
            }

        task_def = self.get_task(task_id)
        
        # Prepare execution context
        result = {
            "task_id": task_id,
            "status": "success",
            "start_time": time.time(),
            "task_definition": task_def,
            "message": f"Task {task_id} validated and ready for execution."
        }

        # Note: Actual model inference and metric computation are handled
        # by the benchmark orchestration layer (run_benchmark.py) to ensure
        # proper timeout handling, logging, and statistical aggregation.
        # This runner focuses on task lifecycle management.

        result["end_time"] = time.time()
        result["duration_seconds"] = result["end_time"] - result["start_time"]

        logger.info(f"Task {task_id} execution completed with status: {result['status']}")
        return result

    def reload_tasks(self) -> int:
        """
        Reload task definitions from disk.

        Returns:
            The number of tasks loaded.
        """
        self._load_tasks()
        return len(self.tasks)

    def list_all_tasks(self) -> List[str]:
        """
        List all available task IDs.

        Returns:
            A list of task ID strings.
        """
        return list(self.tasks.keys())

def main():
    """
    CLI entry point for testing the TaskRunner.
    
    Usage:
        python -m src.tasks.task_runner --list
        python -m src.tasks.task_runner --validate T001
        python -m src.tasks.task_runner --run T001
    """
    import argparse

    parser = argparse.ArgumentParser(description="Task Runner CLI")
    parser.add_argument("--config", type=str, help="Path to task definitions YAML")
    parser.add_argument("--list", action="store_true", help="List all task IDs")
    parser.add_argument("--validate", type=str, help="Validate a specific task ID")
    parser.add_argument("--run", type=str, help="Run a specific task ID")

    args = parser.parse_args()

    runner = TaskRunner(config_path=args.config)

    if args.list:
        tasks = runner.list_all_tasks()
        if not tasks:
            print("No tasks found.")
        else:
            print(f"Found {len(tasks)} tasks:")
            for tid in tasks:
                print(f"  - {tid}")
    
    elif args.validate:
        is_valid, errors = runner.validate_task(args.validate)
        if is_valid:
            print(f"Task {args.validate} is valid.")
        else:
            print(f"Task {args.validate} is invalid:")
            for err in errors:
                print(f"  - {err}")
    
    elif args.run:
        result = runner.run_task(args.run)
        print(f"Execution result: {result}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()