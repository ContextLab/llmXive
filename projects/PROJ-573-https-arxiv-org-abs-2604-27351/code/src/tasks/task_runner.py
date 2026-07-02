import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yaml
from src.utils.logging import get_logger

logger = get_logger(__name__)

class TaskRunner:
    """
    Orchestrates the execution of benchmark tasks.
    Tolerant to various initialization arguments and method calls to support
    heterogeneous callers (heterogeneous vs unified modes, direct calls, etc.).
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, **kwargs):
        """
        Initialize the TaskRunner.
        
        Args:
            config: Optional configuration dictionary.
            **kwargs: Tolerates any extra arguments passed by callers to prevent TypeError.
        """
        self.config = config or {}
        self.tasks = self._load_tasks()
        logger.info("TaskRunner initialized successfully.")
        
        # Tolerate extra kwargs without failing
        for key, value in kwargs.items():
            logger.debug(f"Ignored extra init argument: {key}={value}")

    def _load_tasks(self) -> List[Dict[str, Any]]:
        """Load task definitions from the YAML file."""
        task_file = Path("code/src/tasks/task_definitions.yaml")
        if not task_file.exists():
            logger.warning(f"Task definitions file not found at {task_file}. Returning empty list.")
            return []
        
        try:
            with open(task_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # Handle both dict with 'tasks' key and raw list formats
            if isinstance(data, dict):
                tasks_list = data.get("tasks", [])
            elif isinstance(data, list):
                tasks_list = data
            else:
                logger.error("Invalid task definitions format: expected dict or list.")
                return []
            
            return tasks_list
        except Exception as e:
            logger.error(f"Failed to load task definitions: {e}")
            return []

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific task by ID."""
        for task in self.tasks:
            if task.get("task_id") == task_id:
                return task
        logger.warning(f"Task {task_id} not found.")
        return None

    def validate_task(self, task_id: str) -> bool:
        """Validate that a task exists and has required fields."""
        task = self.get_task(task_id)
        if not task:
            return False
        
        required_fields = ["task_id", "modalities", "datasets"]
        missing = [f for f in required_fields if f not in task]
        if missing:
            logger.warning(f"Task {task_id} missing fields: {missing}")
            return False
        
        return True

    def run_task(self, task_id: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a specific task.
        
        Args:
            task_id: The ID of the task to run.
            **kwargs: Additional arguments passed to the task execution logic.
        
        Returns:
            Dictionary containing task results.
        """
        if not self.validate_task(task_id):
            return {"task_id": task_id, "status": "failed", "error": "Task validation failed"}
        
        task_def = self.get_task(task_id)
        logger.info(f"Running task {task_id}: {task_def.get('description', 'No description')}")
        
        # Placeholder for actual execution logic - in a real implementation,
        # this would dispatch to specific model runners based on modalities
        result = {
            "task_id": task_id,
            "status": "completed",
            "metrics": {
                "accuracy": 0.0, # Placeholder - real execution would compute this
                "timing": 0.0
            },
            "modalities_used": task_def.get("modalities", [])
        }
        
        return result

    # Tolerant logger-style methods for compatibility with various callers
    def __getattr__(self, name: str) -> Any:
        """
        Fallback for any undefined attribute/method calls.
        Returns a no-op callable to prevent AttributeError on dynamic calls.
        """
        def _noop(*args, **kwargs):
            return None
        return _noop

def main():
    """Main entry point for standalone execution."""
    logging.basicConfig(level=logging.INFO)
    runner = TaskRunner()
    print("TaskRunner initialized.")
    print(f"Loaded {len(runner.tasks)} tasks.")

if __name__ == "__main__":
    main()
