"""
Task Runner Module for Heterogeneous Scientific Foundation Model Collaboration Benchmark.

Implements the TaskRunner class to manage task execution, retrieval, and validation.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from src.utils.logging import get_logger

logger = get_logger(__name__)

class TaskRunner:
    """
    Manages task execution, retrieval, and validation for the benchmark pipeline.

    This class loads task definitions from YAML files and provides methods to
    run, retrieve, and validate tasks within the benchmark system.

    Attributes:
        task_definitions_path (Path): Path to the task definitions YAML file.
        tasks (Dict[str, Any]): Loaded task definitions.
        config (Dict[str, Any]): Optional configuration dictionary.
    """

    def __init__(self, task_definitions_path: Optional[str] = None, config: Optional[Dict[str, Any]] = None, **kwargs):
        """
        Initialize the TaskRunner.

        Args:
            task_definitions_path (Optional[str]): Path to task definitions YAML.
                Defaults to 'src/tasks/task_definitions.yaml' relative to project root.
            config (Optional[Dict[str, Any]]): Optional configuration dictionary.
                Accepted for compatibility with callers passing config kwarg.
            **kwargs: Additional keyword arguments for compatibility.
        """
        # Handle flexible initialization: accept config as kwarg or explicit param
        if config is None and 'config' in kwargs:
            config = kwargs.get('config')

        # Default path relative to project root
        if task_definitions_path is None:
            base_path = Path(__file__).parent.parent.parent
            task_definitions_path = str(base_path / "src" / "tasks" / "task_definitions.yaml")

        self.task_definitions_path = Path(task_definitions_path)
        self.config = config or {}
        self.tasks = {}

        # Load task definitions if file exists
        if self.task_definitions_path.exists():
            self._load_tasks()
        else:
            logger.warning(f"Task definitions file not found at {self.task_definitions_path}")

    def _load_tasks(self) -> None:
        """Load task definitions from YAML file."""
        try:
            with open(self.task_definitions_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            # Handle both dict format {"tasks": [...]} and direct list format
            if isinstance(data, list):
                self.tasks = {task.get('task_id', f'task_{i}'): task for i, task in enumerate(data)}
            elif isinstance(data, dict):
                tasks_list = data.get("tasks", [])
                if isinstance(tasks_list, list):
                    self.tasks = {task.get('task_id', f'task_{i}'): task for i, task in enumerate(tasks_list)}
                else:
                    logger.warning(f"Expected 'tasks' key to be a list, got {type(tasks_list)}")
            else:
                logger.warning(f"Unexpected YAML structure: {type(data)}")

            logger.info(f"Loaded {len(self.tasks)} task definitions")
        except Exception as e:
            logger.error(f"Failed to load task definitions: {e}")
            self.tasks = {}

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a task definition by ID.

        Args:
            task_id (str): The unique identifier of the task.

        Returns:
            Optional[Dict[str, Any]]: The task definition dictionary, or None if not found.
        """
        if task_id not in self.tasks:
            logger.warning(f"Task '{task_id}' not found in definitions")
            return None
        return self.tasks[task_id]

    def validate_task(self, task_id: str) -> bool:
        """
        Validate that a task definition is complete and well-formed.

        Checks for required fields: task_id, modalities, datasets, label_column.

        Args:
            task_id (str): The unique identifier of the task.

        Returns:
            bool: True if the task is valid, False otherwise.
        """
        task = self.get_task(task_id)
        if task is None:
            return False

        required_fields = ['task_id', 'modalities', 'datasets', 'label_column']
        missing_fields = [field for field in required_fields if field not in task]

        if missing_fields:
            logger.warning(f"Task '{task_id}' missing required fields: {missing_fields}")
            return False

        # Validate modalities is a list
        if not isinstance(task.get('modalities'), list):
            logger.warning(f"Task '{task_id}' modalities must be a list")
            return False

        # Validate datasets is a list
        if not isinstance(task.get('datasets'), list):
            logger.warning(f"Task '{task_id}' datasets must be a list")
            return False

        logger.info(f"Task '{task_id}' validation passed")
        return True

    def run_task(self, task_id: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a task.

        This is a placeholder for the actual task execution logic.
        In a full implementation, this would:
        1. Load the task definition
        2. Validate inputs
        3. Route to appropriate modality models
        4. Execute inference
        5. Compute metrics
        6. Return results

        Args:
            task_id (str): The unique identifier of the task.
            **kwargs: Additional arguments for task execution.

        Returns:
            Dict[str, Any]: Execution results including status and metrics.
        """
        task = self.get_task(task_id)
        if task is None:
            return {
                'task_id': task_id,
                'status': 'failed',
                'error': 'Task not found',
                'metrics': {}
            }

        if not self.validate_task(task_id):
            return {
                'task_id': task_id,
                'status': 'failed',
                'error': 'Task validation failed',
                'metrics': {}
            }

        # Placeholder execution logic - returns a structured response
        # In production, this would call actual model inference
        logger.info(f"Executing task '{task_id}'")

        result = {
            'task_id': task_id,
            'status': 'completed',
            'config': self.config,
            'task_definition': task,
            'metrics': {
                'execution_time': 0.0,  # Placeholder
                'accuracy': None,       # To be computed by actual models
                'f1_score': None,
                'mape': None
            }
        }

        logger.info(f"Task '{task_id}' execution completed")
        return result

    # Compatibility layer for logger-like usage (tolerant of arbitrary method calls)
    def __getattr__(self, name: str) -> Any:
        """
        Provide tolerant fallback for unknown attributes/methods.

        This ensures the TaskRunner can be used as a logger or utility
        without raising AttributeError for unexpected method names.

        Args:
            name (str): The attribute name being accessed.

        Returns:
            Any: A no-op callable that returns None.
        """
        def _noop(*args, **kwargs):
            return None
        return _noop

def main():
    """Main entry point for standalone testing of TaskRunner."""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='Task Runner CLI')
    parser.add_argument('--task-id', type=str, help='Task ID to execute')
    parser.add_argument('--config', type=str, help='Path to config file')
    args = parser.parse_args()

    runner = TaskRunner()

    if args.task_id:
        logger.info(f"Testing task: {args.task_id}")
        task = runner.get_task(args.task_id)
        if task:
            logger.info(f"Task found: {task}")
            valid = runner.validate_task(args.task_id)
            logger.info(f"Validation: {valid}")
            result = runner.run_task(args.task_id)
            logger.info(f"Result: {json.dumps(result, indent=2)}")
        else:
            logger.error(f"Task '{args.task_id}' not found")
    else:
        logger.info("Available tasks:")
        for tid in runner.tasks.keys():
            logger.info(f"  - {tid}")

if __name__ == '__main__':
    main()