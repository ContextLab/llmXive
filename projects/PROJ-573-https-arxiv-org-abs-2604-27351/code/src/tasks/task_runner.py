"""
Task Runner module for the Heterogeneous Scientific Foundation Model Collaboration Benchmark.

Implements the TaskRunner class to manage task definitions, validation, and execution.
"""
import os
import yaml
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from src.utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)

class TaskRunner:
    """
    Manages task definitions, validation, and execution logic.
    
    Attributes:
        task_definitions_path (Path): Path to the task definitions YAML file.
        tasks (Dict[str, Any]): Loaded task definitions keyed by task_id.
    """
    
    def __init__(self, task_definitions_path: Optional[str] = None):
        """
        Initialize the TaskRunner.
        
        Args:
            task_definitions_path: Path to the task_definitions.yaml file.
                                 If None, uses default location: src/tasks/task_definitions.yaml
        """
        if task_definitions_path is None:
            # Resolve relative to project root (code/)
            project_root = Path(__file__).resolve().parent.parent.parent
            task_definitions_path = project_root / "src" / "tasks" / "task_definitions.yaml"
        
        self.task_definitions_path = Path(task_definitions_path)
        self.tasks: Dict[str, Any] = {}
        self._load_tasks()
    
    def _load_tasks(self) -> None:
        """Load task definitions from the YAML file."""
        if not self.task_definitions_path.exists():
            logger.warning(f"Task definitions file not found: {self.task_definitions_path}")
            self.tasks = {}
            return
        
        try:
            with open(self.task_definitions_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if data is None:
                self.tasks = {}
                logger.info("Task definitions file is empty.")
                return
            
            if isinstance(data, list):
                # List format: [{task_id: ..., ...}, ...]
                self.tasks = {task['task_id']: task for task in data if 'task_id' in task}
            elif isinstance(data, dict):
                # Dict format: {task_id: {...}, ...}
                self.tasks = data
            else:
                logger.error(f"Unexpected format in task definitions: {type(data)}")
                self.tasks = {}
            
            logger.info(f"Loaded {len(self.tasks)} task definitions.")
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file: {e}")
            self.tasks = {}
        except Exception as e:
            logger.error(f"Unexpected error loading tasks: {e}")
            self.tasks = {}
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a task definition by ID.
        
        Args:
            task_id: The unique identifier of the task.
        
        Returns:
            The task definition dictionary, or None if not found.
        """
        task = self.tasks.get(task_id)
        if task is None:
            logger.debug(f"Task definition not found for ID: {task_id}")
        return task
    
    def validate_task(self, task_id: str) -> Tuple[bool, List[str]]:
        """
        Validate a task definition for required fields and consistency.
        
        Args:
            task_id: The unique identifier of the task.
        
        Returns:
            A tuple of (is_valid, list_of_errors).
        """
        task = self.get_task(task_id)
        errors = []
        
        if task is None:
            return False, [f"Task definition not found for ID: {task_id}"]
        
        required_fields = ['task_id', 'modalities', 'label_column']
        
        for field in required_fields:
            if field not in task:
                errors.append(f"Missing required field: {field}")
        
        # Validate modalities list
        if 'modalities' in task:
            if not isinstance(task['modalities'], list):
                errors.append("'modalities' must be a list")
            elif len(task['modalities']) == 0:
                errors.append("'modalities' cannot be empty")
        
        # Validate datasets list if present
        if 'datasets' in task:
            if not isinstance(task['datasets'], list):
                errors.append("'datasets' must be a list")
        
        # Validate label_column is a string
        if 'label_column' in task:
            if not isinstance(task['label_column'], str):
                errors.append("'label_column' must be a string")
        
        is_valid = len(errors) == 0
        if not is_valid:
            logger.warning(f"Task {task_id} validation failed: {errors}")
        
        return is_valid, errors
    
    def run_task(self, task_id: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a task.
        
        This is a placeholder for the actual execution logic.
        In a full implementation, this would load the appropriate models,
        data, and run the inference pipeline based on the task definition.
        
        Args:
            task_id: The unique identifier of the task.
            **kwargs: Additional arguments for execution (e.g., seed, config).
        
        Returns:
            A dictionary containing the execution result.
        
        Raises:
            ValueError: If the task_id is not found or validation fails.
        """
        # Validate first
        is_valid, errors = self.validate_task(task_id)
        if not is_valid:
            raise ValueError(f"Task validation failed: {errors}")
        
        task_def = self.get_task(task_id)
        logger.info(f"Starting execution for task: {task_id}")
        
        start_time = time.time()
        
        # Placeholder execution logic
        # In a real implementation, this would:
        # 1. Load datasets based on task_def['datasets']
        # 2. Route data to appropriate models based on task_def['modalities']
        # 3. Run inference
        # 4. Compute metrics
        # 5. Return results
        
        result = {
            'task_id': task_id,
            'status': 'completed',
            'execution_time': time.time() - start_time,
            'details': {
                'modalities': task_def.get('modalities', []),
                'datasets': task_def.get('datasets', []),
                'label_column': task_def.get('label_column', ''),
                'mode': kwargs.get('mode', 'heterogeneous')
            }
        }
        
        logger.info(f"Task {task_id} completed in {result['execution_time']:.2f}s")
        return result
    
    def list_tasks(self) -> List[str]:
        """
        List all available task IDs.
        
        Returns:
            A list of task IDs.
        """
        return list(self.tasks.keys())


def main():
    """
    Command-line interface for the TaskRunner.
    Usage: python -m src.tasks.task_runner --task-id <ID> --validate
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Task Runner CLI")
    parser.add_argument('--task-id', type=str, help="Task ID to operate on")
    parser.add_argument('--validate', action='store_true', help="Validate the task")
    parser.add_argument('--run', action='store_true', help="Run the task")
    parser.add_argument('--list', action='store_true', help="List all tasks")
    parser.add_argument('--config', type=str, default=None, help="Path to task definitions file")
    
    args = parser.parse_args()
    
    runner = TaskRunner(task_definitions_path=args.config)
    
    if args.list:
        print("Available tasks:")
        for tid in runner.list_tasks():
            print(f"  - {tid}")
        return
    
    if not args.task_id:
        parser.error("Must specify --task-id for validate or run operations")
    
    if args.validate:
        is_valid, errors = runner.validate_task(args.task_id)
        if is_valid:
            print(f"Task {args.task_id} is valid.")
        else:
            print(f"Task {args.task_id} is invalid:")
            for err in errors:
                print(f"  - {err}")
    
    if args.run:
        try:
            result = runner.run_task(args.task_id)
            print(f"Result: {result}")
        except ValueError as e:
            print(f"Error: {e}")
            exit(1)


if __name__ == "__main__":
    main()
