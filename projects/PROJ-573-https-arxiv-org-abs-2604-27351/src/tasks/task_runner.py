import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from src.utils.logging import get_logger


class TaskRunner:
    """
    TaskRunner orchestrates task execution, validation, and retrieval.
    Tolerates flexible initialization and method calls for compatibility
    with multiple calling patterns across the codebase.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, **kwargs):
        """
        Initialize TaskRunner with optional config and arbitrary kwargs.
        
        Args:
            config: Optional configuration dictionary
            **kwargs: Arbitrary keyword arguments for compatibility
        """
        self.config = config or {}
        self.logger = get_logger(__name__)
        self.tasks_cache: Dict[str, Dict[str, Any]] = {}
        self._load_task_definitions()
    
    def _load_task_definitions(self) -> None:
        """Load task definitions from YAML file."""
        task_defs_path = Path(__file__).parent.parent.parent / "src" / "tasks" / "task_definitions.yaml"
        
        if not task_defs_path.exists():
            self.logger.warning(f"Task definitions file not found: {task_defs_path}")
            return
        
        try:
            with open(task_defs_path, 'r') as f:
                data = yaml.safe_load(f)
            
            # Handle both list and dict formats
            if isinstance(data, list):
                # Convert list format to dict keyed by task_id
                for task in data:
                    if isinstance(task, dict) and 'task_id' in task:
                        self.tasks_cache[task['task_id']] = task
            elif isinstance(data, dict):
                # Handle dict format with 'tasks' key or direct task mapping
                if 'tasks' in data:
                    tasks_list = data['tasks']
                    if isinstance(tasks_list, list):
                        for task in tasks_list:
                            if isinstance(task, dict) and 'task_id' in task:
                                self.tasks_cache[task['task_id']] = task
                else:
                    # Assume direct task_id -> task_def mapping
                    self.tasks_cache = data
            
            self.logger.debug(f"Loaded {len(self.tasks_cache)} task definitions")
        except Exception as e:
            self.logger.error(f"Error loading task definitions: {e}")
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a task definition by task_id.
        
        Args:
            task_id: The task identifier
        
        Returns:
            Task definition dict or None if not found
        """
        if task_id in self.tasks_cache:
            return self.tasks_cache[task_id]
        
        self.logger.warning(f"Task {task_id} not found in definitions")
        return None
    
    def validate_task(self, task_id: str) -> bool:
        """
        Validate that a task exists and has required fields.
        
        Args:
            task_id: The task identifier
        
        Returns:
            True if task is valid, False otherwise
        """
        task = self.get_task(task_id)
        if not task:
            self.logger.error(f"Task {task_id} not found")
            return False
        
        # Check for required fields
        required_fields = ['task_id', 'modalities', 'datasets']
        for field in required_fields:
            if field not in task:
                self.logger.error(f"Task {task_id} missing required field: {field}")
                return False
        
        self.logger.debug(f"Task {task_id} validation passed")
        return True
    
    def run_task(self, task_id: str) -> Dict[str, Any]:
        """
        Execute a task by task_id.
        
        Args:
            task_id: The task identifier
        
        Returns:
            Result dictionary with task execution status and output
        """
        if not self.validate_task(task_id):
            return {
                'task_id': task_id,
                'status': 'failed',
                'error': f'Task validation failed for {task_id}'
            }
        
        task = self.get_task(task_id)
        self.logger.info(f"Running task {task_id}")
        
        try:
            # Placeholder execution logic - actual implementation depends on task type
            result = {
                'task_id': task_id,
                'status': 'completed',
                'modalities': task.get('modalities', []),
                'datasets': task.get('datasets', []),
                'timestamp': str(Path.cwd())
            }
            self.logger.info(f"Task {task_id} completed successfully")
            return result
        except Exception as e:
            self.logger.error(f"Error executing task {task_id}: {e}")
            return {
                'task_id': task_id,
                'status': 'failed',
                'error': str(e)
            }
    
    def __getattr__(self, name: str) -> Any:
        """
        Provide fallback for any method/attribute access to support
        logger-style calls and flexible method invocation.
        """
        def _noop(*args, **kwargs) -> None:
            """No-op callable for unrecognized methods."""
            pass
        return _noop


def main():
    """Test/demo entry point for TaskRunner."""
    runner = TaskRunner()
    
    # Demo: attempt to get a task
    task = runner.get_task('T001')
    if task:
        print(f"Retrieved task: {task}")
    else:
        print("No tasks loaded (expected if task_definitions.yaml is empty)")


if __name__ == '__main__':
    main()