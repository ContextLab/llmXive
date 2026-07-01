"""
Single Task Execution Runner
Handles loading and executing individual benchmark tasks.
"""
import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.tasks.task_runner import TaskRunner
from src.utils.logging import get_logger, setup_logger

logger = get_logger(__name__)


def load_task_definition(task_id: str) -> Optional[Dict[str, Any]]:
    """
    Load a specific task definition from the YAML file.
    
    Args:
        task_id: The ID of the task to load.
        
    Returns:
        Task definition dictionary or None.
    """
    task_file = Path("src/tasks/task_definitions.yaml")
    if not task_file.exists():
        logger.error(f"Task definition file not found: {task_file}")
        return None

    try:
        with open(task_file, "r") as f:
            data = yaml.safe_load(f)
        
        # Handle both list and dict formats robustly
        if isinstance(data, list):
            tasks_list = data
        elif isinstance(data, dict):
            tasks_list = data.get("tasks", [])
            if not isinstance(tasks_list, list):
                tasks_list = []
        else:
            tasks_list = []

        for task in tasks_list:
            if task.get("task_id") == task_id:
                return task
        
        logger.warning(f"Task ID {task_id} not found in definitions")
        return None

    except Exception as e:
        logger.error(f"Error loading task definition: {e}")
        return None


def load_modality_configs(modalities: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Load configuration for specified modalities.
    
    Args:
        modalities: List of modality names.
        
    Returns:
        Dictionary mapping modality names to their configs.
    """
    configs = {}
    config_dir = Path("src/benchmark/config/modalities")
    
    for modality in modalities:
        config_path = config_dir / f"{modality}.yaml"
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    configs[modality] = yaml.safe_load(f)
            except Exception as e:
                logger.error(f"Error loading modality config {modality}: {e}")
        else:
            logger.warning(f"Modality config not found: {config_path}")
            
    return configs


def execute_task(task_id: str, add_modality: Optional[str] = None) -> Dict[str, Any]:
    """
    Execute a single benchmark task.
    
    Args:
        task_id: The ID of the task to execute.
        add_modality: Optional additional modality to include.
        
    Returns:
        Execution results dictionary.
    """
    start_time = time.time()
    
    # Load task definition
    task_def = load_task_definition(task_id)
    if not task_def:
        return {
            "status": "error",
            "message": f"Task {task_id} not found",
            "duration": 0
        }

    # Handle additional modality
    modalities = list(task_def.get("modalities", []))
    if add_modality and add_modality not in modalities:
        modalities.append(add_modality)
        logger.info(f"Added modality: {add_modality}")

    # Load modality configs
    modality_configs = load_modality_configs(modalities)

    # Create runner and execute
    runner = TaskRunner()
    result = runner.run_task(task_id)
    
    duration = time.time() - start_time
    
    return {
        "status": result.get("status", "success"),
        "task_id": task_id,
        "modalities": modalities,
        "result": result.get("result"),
        "duration": round(duration, 3),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }


def main():
    """Main entry point for CLI execution."""
    parser = argparse.ArgumentParser(description="Run a single benchmark task")
    parser.add_argument("--task-id", required=True, help="Task ID to execute")
    parser.add_argument("--add-modality", type=str, help="Optional additional modality")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        setup_logger(level="DEBUG")
    else:
        setup_logger(level="INFO")
        
    result = execute_task(args.task_id, args.add_modality)
    
    print(json.dumps(result, indent=2))
    
    # Exit with error code if failed
    sys.exit(0 if result.get("status") == "success" else 1)


if __name__ == "__main__":
    main()
