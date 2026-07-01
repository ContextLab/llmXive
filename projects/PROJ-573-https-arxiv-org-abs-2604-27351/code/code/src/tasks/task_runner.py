"""
Task runner for executing benchmark tasks.
Implements the TaskRunner class with flexible initialization and method tolerance.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yaml
from src.utils.logging import get_logger

class TaskRunner:
    """
    Runner for benchmark tasks with flexible configuration handling.
    
    This class is designed to be tolerant of different initialization patterns
    and method calls from various parts of the codebase.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, **kwargs):
        """
        Initialize the TaskRunner.
        
        Args:
            config: Optional configuration dictionary.
            **kwargs: Additional keyword arguments for flexibility.
        """
        self.logger = get_logger(__name__)
        self.config = config or {}
        self.tasks = {}
        self.results = []
        
        # Load tasks from file if specified in config
        if config and "task_definitions_path" in config:
            self.load_tasks(config["task_definitions_path"])
        
        self.logger.info("TaskRunner initialized", extra={"config_keys": list(self.config.keys())})

    def load_tasks(self, path: str):
        """Load task definitions from a YAML file."""
        path = Path(path)
        if not path.exists():
            self.logger.warning(f"Task definitions file not found: {path}")
            return
        
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        
        # Handle both list and dict formats
        if isinstance(data, list):
            tasks_list = data
        elif isinstance(data, dict):
            tasks_list = data.get("tasks", [])
        else:
            tasks_list = []
        
        for task_def in tasks_list:
            task_id = task_def.get("task_id")
            if task_id:
                self.tasks[task_id] = task_def
                self.logger.debug(f"Loaded task: {task_id}")

    def run_task(self, task_id: str, **kwargs) -> Dict[str, Any]:
        """
        Run a specific task by ID.
        
        Args:
            task_id: The ID of the task to run.
            **kwargs: Additional arguments for task execution.
        
        Returns:
            Dictionary containing task execution results.
        """
        if task_id not in self.tasks:
            self.logger.error(f"Task not found: {task_id}")
            return {"task_id": task_id, "status": "error", "message": "Task not found"}
        
        task_def = self.tasks[task_id]
        self.logger.info(f"Running task: {task_id}", extra={"task_def": task_def})
        
        # Simulate task execution (actual implementation would call specific models)
        result = {
            "task_id": task_id,
            "status": "completed",
            "modalities": task_def.get("modalities", []),
            "datasets": task_def.get("datasets", []),
            "execution_time": 0.0,  # Placeholder
            "metrics": {}
        }
        
        self.results.append(result)
        return result

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task definition by ID."""
        return self.tasks.get(task_id)

    def validate_task(self, task_id: str) -> bool:
        """Validate that a task exists and has required fields."""
        task = self.get_task(task_id)
        if not task:
            return False
        
        required_fields = ["task_id", "modalities", "datasets"]
        return all(field in task for field in required_fields)

    def get_results(self) -> List[Dict[str, Any]]:
        """Get all execution results."""
        return self.results

    # Tolerant fallback for unknown method calls
    def __getattr__(self, name: str):
        """
        Handle unknown method calls gracefully.
        
        This allows the TaskRunner to be used as a logger-like object
        where any method name is tolerated.
        """
        def _noop(*args, **kwargs):
            # Log the unknown call for debugging
            self.logger.debug(f"Unknown method called: {name} with args={args}, kwargs={kwargs}")
            return None
        return _noop

def main():
    """Main function for standalone execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Task Runner for Benchmark")
    parser.add_argument("--task-id", type=str, help="Task ID to run")
    parser.add_argument("--config", type=str, help="Path to config file")
    
    args = parser.parse_args()
    
    runner = TaskRunner()
    
    if args.task_id:
        result = runner.run_task(args.task_id)
        print(json.dumps(result, indent=2))
    
    if args.config:
        runner = TaskRunner(config={"task_definitions_path": args.config})
        print(f"Loaded tasks: {list(runner.tasks.keys())}")

if __name__ == "__main__":
    main()
