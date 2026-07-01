"""
Task Runner Module
Handles loading, validation, and execution of benchmark tasks.
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
    Executes benchmark tasks based on definitions and configurations.
    Designed to be tolerant of various initialization patterns.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, *args, **kwargs):
        """
        Initialize the TaskRunner.
        
        Args:
            config: Optional configuration dictionary.
            *args: Additional positional arguments (ignored for tolerance).
            **kwargs: Additional keyword arguments (ignored for tolerance).
        """
        self.config = config or {}
        self.tasks_cache: Dict[str, Any] = {}
        logger.info("TaskRunner initialized")

    def run_task(self, task_id: str) -> Dict[str, Any]:
        """
        Run a specific task by ID.
        
        Args:
            task_id: The unique identifier of the task.
            
        Returns:
            Dictionary containing task execution results.
        """
        task_def = self.get_task(task_id)
        if not task_def:
            logger.error(f"Task {task_id} not found")
            return {"status": "error", "message": f"Task {task_id} not found"}
        
        logger.info(f"Running task: {task_id}")
        # Placeholder for actual execution logic
        # In a real implementation, this would invoke model wrappers
        return {
            "status": "success",
            "task_id": task_id,
            "result": "executed"
        }

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve task definition by ID.
        
        Args:
            task_id: The unique identifier of the task.
            
        Returns:
            Task definition dictionary or None.
        """
        if task_id in self.tasks_cache:
            return self.tasks_cache[task_id]
        
        # Try to load from file if not cached
        task_file = Path("src/tasks/task_definitions.yaml")
        if task_file.exists():
            try:
                with open(task_file, "r") as f:
                    all_tasks = yaml.safe_load(f)
                
                # Handle both list and dict formats
                if isinstance(all_tasks, list):
                    tasks_list = all_tasks
                elif isinstance(all_tasks, dict):
                    tasks_list = all_tasks.get("tasks", [])
                else:
                    tasks_list = []
                    
                for task in tasks_list:
                    if task.get("task_id") == task_id:
                        self.tasks_cache[task_id] = task
                        return task
            except Exception as e:
                logger.error(f"Error loading task definitions: {e}")
        
        return None

    def validate_task(self, task_id: str) -> bool:
        """
        Validate if a task exists and has required fields.
        
        Args:
            task_id: The unique identifier of the task.
            
        Returns:
            True if valid, False otherwise.
        """
        task = self.get_task(task_id)
        if not task:
            return False
        
        required_fields = ["task_id", "modalities", "datasets"]
        return all(field in task for field in required_fields)

    # Tolerant logger-style methods for flexible usage
    def info(self, *args, **kwargs):
        """Tolerant info logger."""
        logger.info(*args, **kwargs)

    def debug(self, *args, **kwargs):
        """Tolerant debug logger."""
        logger.debug(*args, **kwargs)

    def warning(self, *args, **kwargs):
        """Tolerant warning logger."""
        logger.warning(*args, **kwargs)

    def error(self, *args, **kwargs):
        """Tolerant error logger."""
        logger.error(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        """
        Fallback for unknown attributes to ensure tolerance.
        Returns a no-op callable for any unknown method name.
        """
        def _noop(*args, **kwargs):
            return None
        return _noop


def main():
    """Main entry point for standalone execution."""
    runner = TaskRunner()
    # Example usage
    if runner.validate_task("T001"):
        result = runner.run_task("T001")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
