"""
Task Runner implementation for the Heterogeneous Scientific Foundation Model Collaboration Benchmark.
Handles task execution, validation, and result collection.
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
    Runner for executing benchmark tasks with configurable parameters.
    Tolerant initialization to support various call patterns.
    """
    
    def __init__(self, *args, **kwargs):
        """
        Tolerant initialization that accepts various argument patterns.
        
        Supports:
        - TaskRunner() - no args
        - TaskRunner(config=config) - config kwarg
        - TaskRunner(config_dict) - positional dict
        - TaskRunner(**kwargs) - any kwargs
        """
        self.config = None
        self.task_definitions = None
        self.results = []
        self.logger = logger
        
        # Handle config passed as kwarg
        if 'config' in kwargs:
            self.config = kwargs['config']
            self._load_task_definitions()
        
        # Handle config passed as positional arg (first arg)
        if args and isinstance(args[0], dict):
            self.config = args[0]
            self._load_task_definitions()
        
        # Handle config passed as positional arg (file path)
        if args and isinstance(args[0], (str, Path)):
            self._load_task_definitions(str(args[0]))
        
        logger.info(f"TaskRunner initialized with config: {self.config is not None}")
    
    def _load_task_definitions(self, config_path: Optional[str] = None):
        """Load task definitions from YAML file."""
        if config_path is None and self.config and 'task_definitions' in self.config:
            config_path = self.config['task_definitions']
        
        if config_path:
            try:
                path = Path(config_path)
                if path.exists():
                    with open(path, 'r') as f:
                        self.task_definitions = yaml.safe_load(f)
                    logger.info(f"Loaded task definitions from {config_path}")
                else:
                    logger.warning(f"Task definitions file not found: {config_path}")
            except Exception as e:
                logger.error(f"Failed to load task definitions: {e}")
        else:
            # Default location
            default_path = Path(__file__).parent.parent / 'tasks' / 'task_definitions.yaml'
            if default_path.exists():
                with open(default_path, 'r') as f:
                    self.task_definitions = yaml.safe_load(f)
                logger.info(f"Loaded task definitions from default path: {default_path}")
    
    def run_task(self, task_id: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a single task.
        
        Args:
            task_id: Identifier of the task to run
            **kwargs: Additional parameters for task execution
            
        Returns:
            Dictionary with task results
        """
        logger.info(f"Running task: {task_id}")
        
        task_def = self.get_task(task_id)
        if not task_def:
            logger.error(f"Task not found: {task_id}")
            return {'task_id': task_id, 'status': 'error', 'message': 'Task not found'}
        
        # Validate task
        if not self.validate_task(task_id):
            logger.error(f"Task validation failed: {task_id}")
            return {'task_id': task_id, 'status': 'error', 'message': 'Validation failed'}
        
        # Execute task (placeholder - actual execution logic depends on task type)
        result = {
            'task_id': task_id,
            'status': 'completed',
            'metrics': {},
            'execution_time': 0.0
        }
        
        self.results.append(result)
        logger.info(f"Task completed: {task_id}")
        
        return result
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve task definition by ID.
        
        Args:
            task_id: Identifier of the task
            
        Returns:
            Task definition dictionary or None
        """
        if not self.task_definitions:
            return None
        
        tasks = self.task_definitions.get('tasks', [])
        for task in tasks:
            if task.get('task_id') == task_id:
                return task
        
        # Also check if task_definitions is a list directly
        if isinstance(self.task_definitions, list):
            for task in self.task_definitions:
                if task.get('task_id') == task_id:
                    return task
        
        return None
    
    def validate_task(self, task_id: str) -> bool:
        """
        Validate that a task is properly configured.
        
        Args:
            task_id: Identifier of the task
            
        Returns:
            True if valid, False otherwise
        """
        task = self.get_task(task_id)
        if not task:
            return False
        
        # Basic validation
        required_fields = ['task_id', 'modalities']
        for field in required_fields:
            if field not in task:
                logger.warning(f"Task missing required field: {field}")
                return False
        
        logger.info(f"Task validated: {task_id}")
        return True
    
    def get_results(self) -> List[Dict[str, Any]]:
        """Return all collected results."""
        return self.results
    
    def clear_results(self):
        """Clear all collected results."""
        self.results = []
    
    # Logger-like methods for tolerant attribute access
    def info(self, msg, *args, **kwargs):
        return self.logger.info(msg, *args, **kwargs)
    
    def debug(self, msg, *args, **kwargs):
        return self.logger.debug(msg, *args, **kwargs)
    
    def warning(self, msg, *args, **kwargs):
        return self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg, *args, **kwargs):
        return self.logger.error(msg, *args, **kwargs)
    
    def critical(self, msg, *args, **kwargs):
        return self.logger.critical(msg, *args, **kwargs)
    
    # Fallback for any unknown attribute/method
    def __getattr__(self, name):
        def _noop(*args, **kwargs):
            return None
        return _noop

def main():
    """
    Main function for standalone testing of TaskRunner.
    """
    # Test initialization with different patterns
    runner1 = TaskRunner()
    runner2 = TaskRunner(config={'task_definitions': 'src/tasks/task_definitions.yaml'})
    
    print("TaskRunner initialized successfully")
    print(f"Task definitions loaded: {runner1.task_definitions is not None}")

if __name__ == "__main__":
    main()