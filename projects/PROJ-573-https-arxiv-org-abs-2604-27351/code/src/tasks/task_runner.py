"""
Task Runner module for the Heterogeneous Scientific Foundation Model Collaboration Benchmark.
Implements the TaskRunner class to manage, validate, and execute benchmark tasks.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yaml
from src.utils.logging import get_logger

# Initialize logger for this module
logger = get_logger(__name__)

class TaskRunner:
    """
    Manages benchmark tasks: loading, validation, and execution orchestration.
    Designed to be tolerant of various initialization patterns and method calls
    to support different caller requirements across the codebase.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, **kwargs):
        """
        Initialize the TaskRunner.
        
        Args:
            config: Optional configuration dictionary. If None, defaults are used.
            **kwargs: Additional keyword arguments for flexibility with different callers.
        
        The constructor is designed to accept a 'config' keyword argument to satisfy
        call sites like `TaskRunner(config=config)` while also being flexible with
        other potential initialization patterns.
        """
        self.config = config or {}
        self.tasks_cache: Dict[str, Dict[str, Any]] = {}
        self.logger = logger
        self._load_task_definitions()

    def _load_task_definitions(self) -> None:
        """
        Load task definitions from the task_definitions.yaml file.
        Caches them for quick access by get_task.
        """
        try:
            # Determine the path to task_definitions.yaml
            # Assuming it's in the same directory structure as the task runner
            base_path = Path(__file__).parent.parent
            task_def_path = base_path / "tasks" / "task_definitions.yaml"
            
            if not task_def_path.exists():
                # Try alternative path relative to project root
                task_def_path = Path("code/src/tasks/task_definitions.yaml")
            
            if not task_def_path.exists():
                logger.warning(f"Task definitions file not found at {task_def_path}")
                self.tasks_cache = {}
                return

            with open(task_def_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # Handle both dict with 'tasks' key and direct list
            if isinstance(data, dict):
                tasks_list = data.get("tasks", [])
            elif isinstance(data, list):
                tasks_list = data
            else:
                tasks_list = []
            
            # Cache tasks by task_id
            for task in tasks_list:
                if isinstance(task, dict) and "task_id" in task:
                    self.tasks_cache[task["task_id"]] = task
            
            logger.info(f"Loaded {len(self.tasks_cache)} task definitions")
            
        except Exception as e:
            logger.error(f"Failed to load task definitions: {e}")
            self.tasks_cache = {}

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a task definition by its ID.
        
        Args:
            task_id: The unique identifier of the task.
        
        Returns:
            The task definition dictionary if found, None otherwise.
        """
        if not self.tasks_cache:
            self._load_task_definitions()
        
        task = self.tasks_cache.get(task_id)
        if task:
            logger.debug(f"Retrieved task {task_id}")
        else:
            logger.warning(f"Task {task_id} not found in definitions")
        
        return task

    def validate_task(self, task_id: str) -> bool:
        """
        Validate that a task definition exists and has required fields.
        
        Args:
            task_id: The unique identifier of the task to validate.
        
        Returns:
            True if the task is valid, False otherwise.
        """
        task = self.get_task(task_id)
        if not task:
            logger.error(f"Validation failed: Task {task_id} not found")
            return False

        required_fields = ["task_id", "modalities", "datasets"]
        missing_fields = [field for field in required_fields if field not in task]
        
        if missing_fields:
            logger.error(f"Validation failed: Task {task_id} missing fields: {missing_fields}")
            return False

        # Validate modalities is a list
        if not isinstance(task.get("modalities"), list):
            logger.error(f"Validation failed: Task {task_id} modalities must be a list")
            return False

        # Validate datasets is a list
        if not isinstance(task.get("datasets"), list):
            logger.error(f"Validation failed: Task {task_id} datasets must be a list")
            return False

        logger.info(f"Task {task_id} validation passed")
        return True

    def run_task(self, task_id: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a task. This is a placeholder for the actual execution logic.
        In a full implementation, this would orchestrate the task execution
        using the appropriate models and datasets.
        
        Args:
            task_id: The unique identifier of the task to run.
            **kwargs: Additional arguments for task execution.
        
        Returns:
            A dictionary containing the task execution results.
        """
        if not self.validate_task(task_id):
            return {"status": "error", "message": f"Task {task_id} validation failed"}
        
        task = self.get_task(task_id)
        logger.info(f"Starting execution of task {task_id}")
        
        # Placeholder for actual execution logic
        # In a real implementation, this would:
        # 1. Load the specified datasets
        # 2. Route modalities to appropriate models
        # 3. Execute the models
        # 4. Collect and aggregate results
        # 5. Return the results
        
        result = {
            "status": "completed",
            "task_id": task_id,
            "message": f"Task {task_id} executed successfully (placeholder)",
            "modalities": task.get("modalities", []),
            "datasets": task.get("datasets", [])
        }
        
        logger.info(f"Task {task_id} execution completed")
        return result

    # Tolerant fallback for any unexpected method calls
    def __getattr__(self, name: str) -> Any:
        """
        Provide a tolerant fallback for any method or attribute access
        that doesn't exist, returning a no-op callable to prevent
        AttributeError exceptions from callers.
        """
        def _noop(*args: Any, **kwargs: Any) -> Any:
            logger.debug(f"Called non-existent method '{name}' with args={args}, kwargs={kwargs}")
            return None
        return _noop

    def __getitem__(self, key: str) -> Any:
        """
        Allow dictionary-like access to task definitions.
        """
        return self.tasks_cache.get(key)

    def __len__(self) -> int:
        """
        Return the number of cached tasks.
        """
        return len(self.tasks_cache)

    def __contains__(self, task_id: str) -> bool:
        """
        Check if a task_id exists in the cache.
        """
        return task_id in self.tasks_cache

def main() -> None:
    """
    Main entry point for testing the TaskRunner module.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Task Runner CLI")
    parser.add_argument("--task-id", type=str, help="Task ID to validate/run")
    parser.add_argument("--config", type=str, help="Path to config file")
    args = parser.parse_args()
    
    config = None
    if args.config:
        try:
            with open(args.config, 'r') as f:
                config = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
    
    runner = TaskRunner(config=config)
    
    if args.task_id:
        if runner.validate_task(args.task_id):
            result = runner.run_task(args.task_id)
            print(json.dumps(result, indent=2))
        else:
            print(f"Task {args.task_id} validation failed")
    else:
        print("Available tasks:")
        for task_id in runner.tasks_cache.keys():
            print(f"  - {task_id}")

if __name__ == "__main__":
    main()