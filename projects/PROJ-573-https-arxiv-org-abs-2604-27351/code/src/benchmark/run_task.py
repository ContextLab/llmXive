"""
Single task execution script for the Heterogeneous Scientific Foundation Model Collaboration Benchmark.

Implements T043: Run a single task with optional modality addition.

CLI Usage:
    python -m src.benchmark.run_task --task-id T001 [--add-modality image]

Output:
    JSON object to stdout containing:
    - prediction: The model's prediction
    - modality_contributions: Dict of modality -> contribution score
    - timing: Execution time in seconds
"""
import argparse
import json
import time
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

import yaml
import logging

from src.utils.logging import get_logger, setup_logger
from src.tasks.task_runner import TaskRunner
from src.models.routing import ModalityRouter
from src.utils.missing_handler import handle_missing_modality, build_input_payload
from src.utils.timeout import enforce_timeout, TimeoutError
from src.utils.versioning import update_artifact_timestamp

# Constants
TASK_DEFINITIONS_PATH = project_root / "src" / "tasks" / "task_definitions.yaml"
MODALITIES_CONFIG_DIR = project_root / "src" / "benchmark" / "config" / "modalities"
OUTPUT_PATH = project_root / "data" / "single_task_results"

# Ensure output directory exists
OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

logger = get_logger(__name__)


def load_task_definition(task_id: str) -> Dict[str, Any]:
    """Load a specific task definition from task_definitions.yaml."""
    if not TASK_DEFINITIONS_PATH.exists():
        raise FileNotFoundError(f"Task definitions file not found: {TASK_DEFINITIONS_PATH}")

    with open(TASK_DEFINITIONS_PATH, 'r', encoding='utf-8') as f:
        all_tasks = yaml.safe_load(f)

    if not isinstance(all_tasks, list):
        raise ValueError("Task definitions file must contain a list of tasks.")

    for task in all_tasks:
        if task.get("task_id") == task_id:
            return task

    raise ValueError(f"Task ID '{task_id}' not found in {TASK_DEFINITIONS_PATH}")


def load_modality_configs(modalities: List[str]) -> Dict[str, Dict[str, Any]]:
    """Load configuration for specified modalities."""
    configs = {}
    for modality in modalities:
        config_path = MODALITIES_CONFIG_DIR / f"{modality}.yaml"
        if not config_path.exists():
            logger.warning(f"Modality config not found: {config_path}. Skipping.")
            continue
        
        with open(config_path, 'r', encoding='utf-8') as f:
            configs[modality] = yaml.safe_load(f)
    
    return configs


def execute_task(
    task_id: str, 
    router: ModalityRouter, 
    task_def: Dict[str, Any],
    timeout_seconds: int = 300
) -> Dict[str, Any]:
    """
    Execute a single task using the ModalityRouter.
    
    Args:
        task_id: The ID of the task to run.
        router: The ModalityRouter instance.
        task_def: The task definition dictionary.
        timeout_seconds: Maximum allowed execution time.
    
    Returns:
        Dictionary containing prediction, contributions, and timing.
    """
    start_time = time.time()
    modalities = task_def.get("modalities", [])
    
    # Prepare input data (simulated for this implementation as actual data loading 
    # depends on specific dataset implementations which are assumed to be handled
    # by the model wrappers or missing handler)
    input_data = {}
    
    # Simulate data loading or handle missing modalities
    for modality in modalities:
        # In a real scenario, this would fetch actual data from the dataset
        # For now, we use a placeholder that the model wrapper can handle
        # or the missing handler can replace
        input_data[modality] = None 
    
    # Handle missing modalities if any (logic from FR-009)
    # If a modality is required but missing data, we might need to inject placeholders
    # depending on the condition (heterogeneous vs unified). 
    # Here we assume the router handles the actual data fetching or the placeholder logic.
    
    logger.info(f"Executing task {task_id} with modalities: {modalities}")
    
    try:
        # Enforce timeout
        result = enforce_timeout(
            router.predict, 
            timeout_seconds=timeout_seconds
        )(input_data)
        
        execution_time = time.time() - start_time
        
        return {
            "task_id": task_id,
            "prediction": result.get("prediction", "No prediction"),
            "modality_contributions": result.get("modality_contributions", {}),
            "timing": execution_time,
            "status": "success"
        }
        
    except TimeoutError as e:
        logger.error(f"Task {task_id} timed out after {timeout_seconds}s")
        return {
            "task_id": task_id,
            "prediction": None,
            "modality_contributions": {},
            "timing": time.time() - start_time,
            "status": "timeout",
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Task {task_id} failed with error: {e}", exc_info=True)
        return {
            "task_id": task_id,
            "prediction": None,
            "modality_contributions": {},
            "timing": time.time() - start_time,
            "status": "error",
            "error": str(e)
        }


def main():
    parser = argparse.ArgumentParser(description="Run a single benchmark task.")
    parser.add_argument(
        "--task-id", 
        type=str, 
        required=True, 
        help="The ID of the task to execute (e.g., T001)."
    )
    parser.add_argument(
        "--add-modality", 
        type=str, 
        required=False, 
        default=None,
        help="Optional modality to add to the task configuration."
    )
    parser.add_argument(
        "--timeout", 
        type=int, 
        default=300, 
        help="Timeout per task in seconds (default: 300)."
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=None,
        help="Path to save the JSON output (default: auto-generated based on task_id)."
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logger(level=logging.INFO)
    
    logger.info(f"Starting task execution for {args.task_id}")
    
    # 1. Load Task Definition
    try:
        task_def = load_task_definition(args.task_id)
        logger.info(f"Loaded task definition: {task_def.get('task_id')}")
    except Exception as e:
        logger.error(f"Failed to load task definition: {e}")
        print(json.dumps({"error": str(e), "status": "failed"}))
        sys.exit(1)
    
    # 2. Handle --add-modality
    if args.add_modality:
        logger.info(f"Adding modality: {args.add_modality}")
        current_modalities = task_def.get("modalities", [])
        if args.add_modality not in current_modalities:
            task_def["modalities"] = current_modalities + [args.add_modality]
            logger.info(f"Updated modalities: {task_def['modalities']}")
        else:
            logger.info(f"Modality {args.add_modality} already in task definition.")
    
    # 3. Load Modality Configs
    modalities = task_def.get("modalities", [])
    modality_configs = load_modality_configs(modalities)
    
    if not modality_configs:
        logger.error("No modality configurations found for the task modalities.")
        print(json.dumps({"error": "No valid modality configs", "status": "failed"}))
        sys.exit(1)
    
    # 4. Initialize Router
    # The router is expected to load models based on the configs passed or internally
    router = ModalityRouter(configs=modality_configs)
    
    # 5. Execute Task
    result = execute_task(
        task_id=args.task_id,
        router=router,
        task_def=task_def,
        timeout_seconds=args.timeout
    )
    
    # 6. Output Result
    output_json = json.dumps(result, indent=2)
    print(output_json)
    
    # 7. Save to file if requested or by default
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = OUTPUT_PATH / f"task_{args.task_id}_result.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_json)
    
    logger.info(f"Result saved to {output_path}")
    
    # Update artifact timestamp for versioning
    update_artifact_timestamp(str(output_path))
    
    if result["status"] != "success":
        sys.exit(1)


if __name__ == "__main__":
    main()
