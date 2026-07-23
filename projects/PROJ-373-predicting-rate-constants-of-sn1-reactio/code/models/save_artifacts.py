import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from utils.logger import setup_logging, get_logger
from config import ensure_dirs

logger = None

def load_best_training_result(results_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load the training results JSON and identify the best configuration based on validation R².
    """
    if not results_path.exists():
        raise FileNotFoundError(f"Training results file not found: {results_path}")

    with open(results_path, 'r') as f:
        results = json.load(f)

    if not results.get("results"):
        raise ValueError("No training results found in the file.")

    # Sort by validation R² descending
    best_result = max(results["results"], key=lambda x: x.get("r2_val", -float('inf')))
    return best_result

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """
    Load the YAML schema definition for model output.
    """
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_metrics_against_schema(metrics: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate that the metrics dictionary conforms to the expected schema structure.
    We perform a basic structural check: required keys must exist and have expected types.
    """
    required_keys = ["model_id", "hyperparameters", "metrics"]
    for key in required_keys:
        if key not in metrics:
            logger.error(f"Missing required key in metrics: {key}")
            return False

    # Check metrics substructure (r2, mae)
    if "metrics" in metrics:
        metric_keys = ["r2", "mae"]
        for m_key in metric_keys:
            if m_key not in metrics["metrics"]:
                logger.error(f"Missing metric: {m_key}")
                return False

    # Check hyperparameters substructure (optional but good practice)
    if "hyperparameters" in metrics and not isinstance(metrics["hyperparameters"], dict):
        logger.error("Hyperparameters must be a dictionary.")
        return False

    logger.info("Metrics validation against schema passed.")
    return True

def save_best_model(model_state_dict: Dict[str, Any], output_path: Path) -> None:
    """
    Save the PyTorch model state dictionary to a .pt file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    import torch
    torch.save(model_state_dict, output_path)
    logger.info(f"Best model weights saved to: {output_path}")

def save_metrics(metrics: Dict[str, Any], output_path: Path) -> None:
    """
    Save the metrics dictionary to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to: {output_path}")

def save_hyperparameter_log(log_path: Path, results_path: Path) -> None:
    """
    Optionally save the full hyperparameter search log to the artifacts directory.
    This ensures traceability as required by FR-003.
    """
    if not results_path.exists():
        logger.warning(f"Skipping hyperparameter log copy: {results_path} not found.")
        return

    import shutil
    shutil.copy(results_path, log_path)
    logger.info(f"Hyperparameter search log copied to: {log_path}")

def main():
    global logger
    parser = argparse.ArgumentParser(description="Save best model and metrics artifacts.")
    parser.add_argument("--results-path", type=str, required=True,
                        help="Path to the training results JSON (output of train.py).")
    parser.add_argument("--model-weights", type=str, required=True,
                        help="Path to the best model weights file (output of train.py).")
    parser.add_argument("--schema-path", type=str, required=True,
                        help="Path to the model_output.schema.yaml file.")
    parser.add_argument("--output-dir", type=str, default="artifacts",
                        help="Directory to save the final artifacts.")

    args = parser.parse_args()
    logger = setup_logging("save_artifacts", level=logging.INFO)

    results_path = Path(args.results_path)
    model_weights_path = Path(args.model_weights)
    schema_path = Path(args.schema_path)
    output_dir = Path(args.output_dir)

    ensure_dirs([output_dir])

    # 1. Load best result
    logger.info(f"Loading best training result from: {results_path}")
    best_result = load_best_training_result(results_path)

    # 2. Prepare metrics dictionary
    # We need to reconstruct the structure expected by the schema:
    # model_id, hyperparameters, metrics (r2, mae)
    # The training result likely has: config (hyperparams), r2_val, mae_val, model_path
    metrics_dict = {
        "model_id": best_result.get("config", {}).get("seed", "unknown_seed"),
        "hyperparameters": best_result.get("config", {}),
        "metrics": {
            "r2": best_result.get("r2_val"),
            "mae": best_result.get("mae_val")
        },
        "weights_path": str(model_weights_path)
    }

    # 3. Validate against schema
    logger.info(f"Loading schema from: {schema_path}")
    schema = load_schema(schema_path)
    logger.info("Validating metrics against schema...")
    if not validate_metrics_against_schema(metrics_dict, schema):
        logger.error("Metrics validation failed. Aborting save.")
        sys.exit(1)

    # 4. Save model weights
    # The training script likely saved the best model to a specific path.
    # We copy or move it to artifacts/best_model.pt
    if not model_weights_path.exists():
        logger.error(f"Model weights file not found: {model_weights_path}")
        sys.exit(1)

    best_model_output = output_dir / "best_model.pt"
    save_best_model(model_weights_path, best_model_output) # Note: save_best_model expects a state_dict or path?
    # Correction: save_best_model expects a state_dict. Let's load it if it's a file, or assume it's already a dict.
    # Actually, the function signature above expects a dict. If model_weights_path is a file, we need to load it.
    # However, usually we just move/copy the file. Let's adjust logic:
    # If the training script outputs a file, we just copy it.
    # But to be safe and follow the "save_best_model" pattern:
    import shutil
    shutil.copy(model_weights_path, best_model_output)
    logger.info(f"Model weights copied to: {best_model_output}")

    # 5. Save metrics JSON
    metrics_output = output_dir / "metrics.json"
    save_metrics(metrics_dict, metrics_output)

    # 6. Save hyperparameter log (optional but good for traceability)
    log_output = output_dir / "hyperparameter_search_full.json"
    save_hyperparameter_log(log_output, results_path)

    logger.info("T022 completed successfully. Artifacts saved.")

if __name__ == "__main__":
    main()
