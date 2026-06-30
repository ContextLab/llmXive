"""
Task Runner module for the Heterogeneous Scientific Foundation Model Collaboration Benchmark.

Implements the TaskRunner class to manage task execution, retrieval, and validation.
"""
import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

# Import logging utilities from existing API
from src.utils.logging import get_logger
from src.utils.checksum_utils import compute_file_sha256, load_state_file, save_state_file, update_artifact_hash
from src.utils.versioning import update_artifact_timestamp

# Configure logger
logger = get_logger(__name__)


class TaskRunner:
    """
    Manages task definitions, validation, and execution logic.

    Tasks are loaded from a YAML definition file and validated against
    the project's task schema contract.
    """

    def __init__(self, task_definitions_path: Optional[str] = None, state_path: Optional[str] = None):
        """
        Initialize the TaskRunner.

        Args:
            task_definitions_path: Path to the task_definitions.yaml file.
            state_path: Path to the project state YAML file for checksum tracking.
        """
        self.project_root = Path(__file__).resolve().parent.parent.parent
        
        # Default paths relative to project root
        if task_definitions_path is None:
            self.task_definitions_path = self.project_root / "src" / "tasks" / "task_definitions.yaml"
        else:
            self.task_definitions_path = Path(task_definitions_path)

        if state_path is None:
            self.state_path = self.project_root / "state" / "projects" / "PROJ-573-https-arxiv-org-abs-2604-27351.yaml"
        else:
            self.state_path = Path(state_path)

        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._load_tasks()

        # Ensure state directory exists
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"TaskRunner initialized. Definitions: {self.task_definitions_path}, State: {self.state_path}")


    def _load_tasks(self) -> None:
        """Load task definitions from the YAML file."""
        if not self.task_definitions_path.exists():
            logger.warning(f"Task definitions file not found: {self.task_definitions_path}. Initializing empty task registry.")
            self._tasks = {}
            return

        try:
            with open(self.task_definitions_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if data is None:
                self._tasks = {}
            elif isinstance(data, dict):
                # Support both list of tasks and dict of tasks
                if 'tasks' in data and isinstance(data['tasks'], list):
                    self._tasks = {task['task_id']: task for task in data['tasks']}
                elif 'tasks' in data and isinstance(data['tasks'], dict):
                    self._tasks = data['tasks']
                else:
                    # Assume the root is a dict of task_id -> task_def
                    self._tasks = data
            
            logger.info(f"Loaded {len(self._tasks)} task definitions.")
        except Exception as e:
            logger.error(f"Failed to load task definitions: {e}")
            self._tasks = {}


    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a task definition by ID.

        Args:
            task_id: The unique identifier of the task.

        Returns:
            The task definition dictionary, or None if not found.
        """
        task = self._tasks.get(task_id)
        if task:
            logger.debug(f"Retrieved task: {task_id}")
        else:
            logger.warning(f"Task not found: {task_id}")
        return task


    def validate_task(self, task_id: str) -> bool:
        """
        Validate a task definition against the schema contract.

        Validates that the task exists and contains required fields:
        - task_id
        - modalities (list)
        - datasets (list)
        - label_column (string)

        Args:
            task_id: The unique identifier of the task to validate.

        Returns:
            True if the task is valid, False otherwise.
        """
        task = self.get_task(task_id)
        if task is None:
            logger.error(f"Validation failed: Task '{task_id}' does not exist.")
            return False

        required_fields = ['task_id', 'modalities', 'datasets', 'label_column']
        missing_fields = [field for field in required_fields if field not in task]

        if missing_fields:
            logger.error(f"Validation failed for task '{task_id}': Missing required fields: {missing_fields}")
            return False

        # Type checks
        if not isinstance(task['modalities'], list):
            logger.error(f"Validation failed for task '{task_id}': 'modalities' must be a list.")
            return False

        if not isinstance(task['datasets'], list):
            logger.error(f"Validation failed for task '{task_id}': 'datasets' must be a list.")
            return False

        if not isinstance(task['label_column'], str):
            logger.error(f"Validation failed for task '{task_id}': 'label_column' must be a string.")
            return False

        logger.info(f"Validation successful for task: {task_id}")
        return True


    def run_task(self, task_id: str) -> Dict[str, Any]:
        """
        Execute a task.

        This is a placeholder for the actual execution logic which would involve:
        1. Loading the dataset(s) specified in the task.
        2. Preprocessing data based on modalities.
        3. Running the appropriate model(s).
        4. Computing metrics.
        5. Storing results.

        Currently, it validates the task and returns a simulated result structure
        to demonstrate the interface. In a full implementation, this would call
        the model wrappers and evaluation modules.

        Args:
            task_id: The unique identifier of the task to run.

        Returns:
            A dictionary containing the task execution result.
        
        Raises:
            ValueError: If the task ID is not found or validation fails.
        """
        # Validate task before running
        if not self.validate_task(task_id):
            raise ValueError(f"Cannot run task '{task_id}': Validation failed.")

        task_def = self.get_task(task_id)
        logger.info(f"Starting execution of task: {task_id}")

        # Simulate execution steps (Actual implementation would integrate with models and data loaders)
        result = {
            "task_id": task_id,
            "status": "completed",
            "modalities_processed": task_def['modalities'],
            "datasets_used": task_def['datasets'],
            "label_column": task_def['label_column'],
            "metrics": {
                "accuracy": 0.0, # Placeholder - real implementation calculates this
                "f1_score": 0.0,
                "mape": 0.0
            },
            "execution_time_seconds": 0.0,
            "timestamp": None # Set by versioning/update logic if needed
        }

        # Update state file with artifact hash if task definition changed
        # (In a real scenario, we'd track the hash of the task definition file itself)
        if self.state_path.exists():
            try:
                checksum = compute_file_sha256(self.task_definitions_path)
                state_data = load_state_file(self.state_path)
                if 'artifact_hashes' not in state_data:
                    state_data['artifact_hashes'] = {}
                
                # Track the task definitions file hash
                file_key = str(self.task_definitions_path.relative_to(self.project_root))
                update_artifact_hash(state_data, file_key, checksum)
                
                # Update timestamp
                update_artifact_timestamp(self.state_path)
                
                save_state_file(self.state_path, state_data)
                logger.debug(f"Updated state file with task definitions checksum.")
            except Exception as e:
                logger.warning(f"Could not update state file: {e}")

        logger.info(f"Task {task_id} execution finished.")
        return result


    def list_tasks(self) -> List[str]:
        """
        List all available task IDs.

        Returns:
            A list of task ID strings.
        """
        return list(self._tasks.keys())


def main():
    """
    Main entry point for running the task runner as a script.
    Demonstrates usage by loading tasks, validating one, and running it.
    """
    # Initialize runner
    runner = TaskRunner()

    # List available tasks
    tasks = runner.list_tasks()
    print(f"Available tasks: {tasks}")

    if not tasks:
        print("No tasks found in definitions file.")
        return

    # Pick the first task for demonstration
    target_task = tasks[0]
    print(f"Validating task: {target_task}")
    
    if runner.validate_task(target_task):
        print(f"Running task: {target_task}")
        try:
            result = runner.run_task(target_task)
            print(f"Result: {result}")
        except Exception as e:
            print(f"Error running task: {e}")
    else:
        print(f"Task {target_task} failed validation.")


if __name__ == "__main__":
    main()
