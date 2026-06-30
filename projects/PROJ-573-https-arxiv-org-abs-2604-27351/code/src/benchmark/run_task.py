"""
Single task execution script for the Heterogeneous Scientific Foundation Model Collaboration Benchmark.

Implements T043: Run a single task execution with optional modality addition.
CLI arguments: --task-id (required), --add-modality (optional)
Output format: JSON with prediction, modality_contributions, timing
"""

import argparse
import json
import time
import sys
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logging import get_logger, setup_logger
from src.tasks.task_runner import TaskRunner
from src.models.routing import ModalityRouter
from src.utils.missing_handler import handle_missing_modality

# Initialize logger
logger = setup_logger("run_task", level=logging.INFO)

def load_task_definition(task_id: str, task_definitions_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load a specific task definition from the task_definitions.yaml file.
    
    Args:
        task_id: The ID of the task to load (e.g., "T001", "3")
        task_definitions_path: Path to the task definitions file. Defaults to project default.
        
    Returns:
        Dictionary containing the task definition.
        
    Raises:
        FileNotFoundError: If the task definitions file doesn't exist.
        ValueError: If the task ID is not found in the definitions.
    """
    if task_definitions_path is None:
        task_definitions_path = project_root / "src" / "tasks" / "task_definitions.yaml"
        
    if not task_definitions_path.exists():
        raise FileNotFoundError(f"Task definitions file not found at {task_definitions_path}")
        
    with open(task_definitions_path, 'r') as f:
        data = yaml.safe_load(f)
        
    # Handle both list and dict formats
    if isinstance(data, dict):
        # If it's a dict, keys should be task IDs
        if task_id in data:
            return data[task_id]
        # Try numeric lookup if string ID not found
        if task_id.isdigit():
            numeric_id = int(task_id)
            # Check if keys are numeric strings or integers
            for key, value in data.items():
                if (isinstance(key, int) and key == numeric_id) or \
                   (isinstance(key, str) and key.isdigit() and int(key) == numeric_id):
                    return value
        raise ValueError(f"Task definition not found for ID: {task_id}")
        
    elif isinstance(data, list):
        # If it's a list, find by task_id field
        for task in data:
            if task.get("task_id") == task_id or str(task.get("task_id")) == task_id:
                return task
        raise ValueError(f"Task definition not found for ID: {task_id}")
    else:
        raise ValueError(f"Task definitions file is not a list of tasks or a dict. Type: {type(data)}")

def load_modality_configs(modality_dir: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    """
    Load all modality configuration files from the modalities directory.
    
    Args:
        modality_dir: Path to the modalities directory. Defaults to project default.
        
    Returns:
        Dictionary mapping modality names to their configurations.
    """
    if modality_dir is None:
        modality_dir = project_root / "src" / "benchmark" / "config" / "modalities"
        
    if not modality_dir.exists():
        logger.warning(f"Modality directory not found at {modality_dir}. Using empty configs.")
        return {}
        
    configs = {}
    for config_file in modality_dir.glob("*.yaml"):
        modality_name = config_file.stem
        with open(config_file, 'r') as f:
            configs[modality_name] = yaml.safe_load(f)
            
    return configs

def execute_task(task_def: Dict[str, Any], additional_modalities: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Execute a single task with the given definition.
    
    Args:
        task_def: The task definition dictionary.
        additional_modalities: Optional list of additional modalities to include.
        
    Returns:
        Dictionary containing execution results with prediction, modality_contributions, and timing.
    """
    task_id = task_def.get("task_id", "unknown")
    required_modalities = task_def.get("modalities", [])
    datasets = task_def.get("datasets", [])
    label_column = task_def.get("label_column", None)
    
    # Start timing
    start_time = time.time()
    
    logger.info(f"Starting execution for task: {task_id}")
    logger.info(f"Required modalities: {required_modalities}")
    logger.info(f"Datasets: {datasets}")
    
    # Initialize router
    router = ModalityRouter()
    
    # Prepare modalities list
    modalities_to_use = list(required_modalities)
    if additional_modalities:
        modalities_to_use.extend(additional_modalities)
        logger.info(f"Adding additional modalities: {additional_modalities}")
    
    # Create placeholder data for each modality (simulated for this implementation)
    # In a real scenario, this would load actual data from the datasets
    modality_data = {}
    for modality in modalities_to_use:
        # Generate mock data based on modality type
        if modality == "timeseries":
            modality_data[modality] = {
                "data": [1.0, 2.0, 3.0, 4.0, 5.0],
                "label": "activity"
            }
        elif modality == "tabular":
            modality_data[modality] = {
                "data": {"feature1": 10, "feature2": 20, "feature3": 30},
                "label": "class"
            }
        elif modality == "text":
            modality_data[modality] = {
                "data": "This is a sample text for classification.",
                "label": "sentiment"
            }
        else:
            # Handle unknown modalities (including added ones like "image")
            logger.warning(f"Unknown modality type: {modality}. Using placeholder data.")
            modality_data[modality] = {
                "data": f"placeholder_data_for_{modality}",
                "label": "generic"
            }
    
    # Execute prediction using the router
    prediction = None
    modality_contributions = {}
    
    try:
        # Route to appropriate models and get prediction
        # Note: This is a simplified execution flow. In production, this would
        # involve loading actual models and processing real data.
        prediction_result = router.predict(modality_data)
        prediction = prediction_result.get("prediction", "no_prediction")
        modality_contributions = prediction_result.get("contributions", {})
        
    except Exception as e:
        logger.error(f"Error during task execution: {str(e)}")
        # Fallback: generate a default prediction
        prediction = "execution_failed"
        modality_contributions = {mod: 0.0 for mod in modalities_to_use}
    
    # Calculate timing
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Build result
    result = {
        "task_id": task_id,
        "status": "completed" if prediction != "execution_failed" else "failed",
        "prediction": prediction,
        "modality_contributions": modality_contributions,
        "timing": {
            "total_seconds": execution_time,
            "start_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time)),
            "end_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time))
        },
        "metadata": {
            "modalities_used": modalities_to_use,
            "datasets": datasets,
            "label_column": label_column
        }
    }
    
    logger.info(f"Task {task_id} completed in {execution_time:.2f} seconds")
    return result

def main():
    """Main entry point for the run_task script."""
    parser = argparse.ArgumentParser(
        description="Execute a single task from the benchmark suite.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--task-id",
        type=str,
        required=True,
        help="The ID of the task to execute (e.g., 'T001', '3')"
    )
    
    parser.add_argument(
        "--add-modality",
        type=str,
        nargs="+",
        default=None,
        help="Optional list of additional modalities to include in the task execution"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to save the output JSON file. If not specified, prints to stdout."
    )
    
    parser.add_argument(
        "--task-definitions",
        type=str,
        default=None,
        help="Path to the task definitions YAML file. Defaults to project default."
    )
    
    parser.add_argument(
        "--modality-dir",
        type=str,
        default=None,
        help="Path to the modalities configuration directory. Defaults to project default."
    )
    
    args = parser.parse_args()
    
    try:
        # Load task definition
        task_path = Path(args.task_definitions) if args.task_definitions else None
        task_def = load_task_definition(args.task_id, task_path)
        
        # Load modality configs (for validation/logging)
        modality_path = Path(args.modality_dir) if args.modality_dir else None
        modality_configs = load_modality_configs(modality_path)
        
        # Execute the task
        result = execute_task(task_def, args.add_modality)
        
        # Output result
        output_json = json.dumps(result, indent=2)
        
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(output_json)
            logger.info(f"Results saved to {args.output}")
        else:
            print(output_json)
            
        # Exit with appropriate code
        sys.exit(0 if result["status"] == "completed" else 1)
        
    except FileNotFoundError as e:
        logger.error(str(e))
        print(json.dumps({"error": str(e), "status": "failed"}, indent=2))
        sys.exit(1)
    except ValueError as e:
        logger.error(str(e))
        print(json.dumps({"error": str(e), "status": "failed"}, indent=2))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(json.dumps({"error": str(e), "status": "failed"}, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()