import argparse
import json
import time
import sys
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Import from existing API surface
from src.utils.logging import get_logger, setup_logger
from src.tasks.task_runner import TaskRunner
from src.models.routing import ModalityRouter
from src.utils.missing_handler import handle_missing_modality, build_input_payload

# Configure logger for this module
logger = setup_logger("run_task", level=logging.INFO)

def load_task_definition(task_id: str, task_file: str = "src/tasks/task_definitions.yaml") -> Optional[Dict[str, Any]]:
    """
    Load a specific task definition from the YAML file.
    Returns None if task_id is not found.
    """
    task_path = Path(task_file)
    if not task_path.exists():
        logger.error(f"Task definitions file not found: {task_path}")
        return None

    try:
        with open(task_path, 'r') as f:
            definitions = yaml.safe_load(f)

        if not definitions or 'tasks' not in definitions:
            logger.error("Task definitions file is empty or missing 'tasks' key")
            return None

        # Search for task by ID (handle both string and int comparisons)
        for task in definitions['tasks']:
            if str(task.get('task_id', '')) == str(task_id):
                return task

        logger.warning(f"Task ID '{task_id}' not found in definitions.")
        return None

    except Exception as e:
        logger.error(f"Error loading task definitions: {e}")
        return None

def load_modality_configs(modality_dir: str = "src/benchmark/config/modalities") -> Dict[str, Dict[str, Any]]:
    """
    Load all modality configuration files from the specified directory.
    Returns a dictionary mapping modality names to their configs.
    """
    modality_path = Path(modality_dir)
    configs = {}

    if not modality_path.exists():
        logger.warning(f"Modality config directory not found: {modality_path}")
        return configs

    for yaml_file in modality_path.glob("*.yaml"):
        try:
            with open(yaml_file, 'r') as f:
                config = yaml.safe_load(f)
                if config and 'model_id' in config:
                    # Use filename as modality key
                    modality_name = yaml_file.stem
                    configs[modality_name] = config
                    logger.info(f"Loaded modality config: {modality_name}")
        except Exception as e:
            logger.error(f"Error loading modality config {yaml_file}: {e}")

    return configs

def execute_task(task_def: Dict[str, Any], modality_configs: Dict[str, Dict[str, Any]], 
                 added_modality: Optional[str] = None) -> Dict[str, Any]:
    """
    Execute a single task based on its definition and available modality configs.
    Handles missing modalities and routing.
    """
    task_id = task_def.get('task_id', 'unknown')
    modalities = task_def.get('modalities', [])
    datasets = task_def.get('datasets', [])
    
    start_time = time.time()
    result = {
        "task_id": task_id,
        "status": "failed",
        "prediction": None,
        "modality_contributions": {},
        "timing": {},
        "error": None
    }

    try:
        # Handle added modality
        if added_modality:
            if added_modality not in modalities:
                modalities = modalities + [added_modality]
                logger.info(f"Added modality '{added_modality}' to task {task_id}")
            
            # Check if config exists for added modality
            if added_modality not in modality_configs:
                logger.warning(f"No config found for added modality: {added_modality}")
                # Attempt to create a placeholder config or use missing handler
                modality_configs[added_modality] = {"model_id": f"placeholder_{added_modality}", "model_type": "placeholder"}

        # Identify missing modalities
        missing_modalities = []
        for mod in modalities:
            if mod not in modality_configs:
                missing_modalities.append(mod)

        # Handle missing modalities
        if missing_modalities:
            for mod in missing_modalities:
                handle_missing_modality(task_id, mod, "heterogeneous")
            
            # Remove missing modalities from execution list for heterogeneous mode
            # In heterogeneous mode, we skip missing modalities
            available_modalities = [m for m in modalities if m in modality_configs]
            if not available_modalities:
                raise ValueError("No available modalities to execute task")
        else:
            available_modalities = modalities

        # Initialize router and load models
        router = ModalityRouter()
        
        # Load models for available modalities
        loaded_models = {}
        for mod in available_modalities:
            config = modality_configs[mod]
            model_id = config.get('model_id')
            model_type = config.get('model_type', mod)
            
            logger.info(f"Loading model for {mod}: {model_id}")
            # Use router to load appropriate model wrapper based on type
            model = router.get_model(model_type, model_id)
            if model:
                loaded_models[mod] = model
                result["modality_contributions"][mod] = "loaded"
            else:
                logger.warning(f"Failed to load model for {mod}")

        if not loaded_models:
            raise ValueError("No models could be loaded for task execution")

        # Simulate data loading (in real scenario, download_dataset would be called)
        # For now, we create synthetic input data based on modality types
        input_data = {}
        for mod in loaded_models.keys():
            # Create minimal synthetic input for each modality
            if mod == "timeseries":
                input_data[mod] = {"data": [1.0, 2.0, 3.0, 4.0, 5.0], "label": "activity"}
            elif mod == "tabular":
                input_data[mod] = {"data": [[1, 2], [3, 4]], "label": "class"}
            elif mod == "text":
                input_data[mod] = {"data": "sample text input", "label": "sentiment"}
            else:
                input_data[mod] = {"data": "generic input", "label": "unknown"}

        # Execute prediction using router
        logger.info(f"Executing prediction for task {task_id} with modalities: {list(loaded_models.keys())}")
        prediction = router.predict(input_data)
        
        end_time = time.time()
        result["status"] = "success"
        result["prediction"] = prediction
        result["timing"]["total_seconds"] = round(end_time - start_time, 3)
        result["timing"]["models_loaded"] = len(loaded_models)

    except Exception as e:
        logger.error(f"Task execution failed: {e}", exc_info=True)
        result["error"] = str(e)
        result["timing"]["total_seconds"] = round(time.time() - start_time, 3)

    return result

def main():
    """Main entry point for single task execution."""
    parser = argparse.ArgumentParser(description="Execute a single benchmark task")
    parser.add_argument("--task-id", required=True, help="Task ID to execute (e.g., T001)")
    parser.add_argument("--add-modality", type=str, default=None, 
                        help="Optional modality to add to the task definition")
    parser.add_argument("--task-file", type=str, default="src/tasks/task_definitions.yaml",
                        help="Path to task definitions YAML file")
    parser.add_argument("--modality-dir", type=str, default="src/benchmark/config/modalities",
                        help="Directory containing modality config files")
    
    args = parser.parse_args()

    logger.info(f"Starting task execution for: {args.task_id}")

    # Load task definition
    task_def = load_task_definition(args.task_id, args.task_file)
    if not task_def:
        error_result = {
            "error": f"Task definition not found for ID: {args.task_id}",
            "status": "failed"
        }
        print(json.dumps(error_result))
        sys.exit(1)

    # Load modality configs
    modality_configs = load_modality_configs(args.modality_dir)
    if not modality_configs:
        logger.warning("No modality configurations found. Execution may fail.")

    # Execute task
    result = execute_task(task_def, modality_configs, args.add_modality)

    # Output result as JSON
    print(json.dumps(result, indent=2))

    # Exit with error code if failed
    if result["status"] == "failed":
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()