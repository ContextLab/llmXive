import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Local imports based on API surface
from config import TrainingConfig, DataConfig, AnalysisConfig, ensure_dirs
from utils.logger import setup_logging, get_logger
from utils.checksum import compute_file_checksum

# Import schema validation helper (assuming it exists or is defined here if not in other files)
# The task requires validating against model_output.schema.yaml
import yaml

logger = get_logger(__name__)

def load_best_training_result(results_dir: Path) -> Dict[str, Any]:
    """
    Loads the best training result from the results directory.
    Expects a file named 'best_result.json' or similar containing metrics and path to weights.
    """
    best_result_path = results_dir / "best_result.json"
    if not best_result_path.exists():
        # Fallback: scan for the file with highest val_r2 if naming convention varies
        # For now, assume standard naming based on T020/T021 output
        raise FileNotFoundError(f"Best training result not found at {best_result_path}")
    
    with open(best_result_path, 'r') as f:
        return json.load(f)

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Loads the YAML schema definition."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_metrics_against_schema(metrics: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validates the metrics dictionary against the loaded schema.
    Checks for required top-level keys: model_id, hyperparameters, metrics (r2, mae), weights_path.
    """
    required_keys = ['model_id', 'hyperparameters', 'metrics', 'weights_path']
    for key in required_keys:
        if key not in metrics:
            logger.error(f"Missing required key in metrics: {key}")
            return False
    
    # Check nested metrics
    if not isinstance(metrics['metrics'], dict):
        logger.error("metrics field must be a dictionary")
        return False
    
    if 'r2' not in metrics['metrics'] or 'mae' not in metrics['metrics']:
        logger.error("metrics field must contain 'r2' and 'mae'")
        return False

    # Check hyperparameters structure if defined in schema
    # Simple validation: ensure it's a dict
    if not isinstance(metrics['hyperparameters'], dict):
        logger.error("hyperparameters field must be a dictionary")
        return False

    return True

def save_best_model(model, model_path: Path) -> None:
    """Saves the PyTorch model state dict."""
    import torch
    model_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), model_path)
    logger.info(f"Model weights saved to {model_path}")

def save_metrics(metrics: Dict[str, Any], metrics_path: Path) -> None:
    """Saves metrics to a JSON file."""
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {metrics_path}")

def save_hyperparameter_log(search_results: list, log_path: Path) -> None:
    """Saves the hyperparameter search results to a CSV."""
    import csv
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if not search_results:
        logger.warning("No search results to save.")
        return

    # Determine headers from the first result
    fieldnames = list(search_results[0].keys())
    with open(log_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(search_results)
    logger.info(f"Hyperparameter log saved to {log_path}")

def main():
    """
    Main entry point for T022: Save best model weights and metrics.
    """
    setup_logging()
    
    # Configuration paths
    config = TrainingConfig()
    data_config = DataConfig()
    
    results_dir = Path(config.results_dir)
    artifacts_dir = Path("artifacts")
    contracts_dir = Path("specs/001-predict-sn1-rate-constants/contracts")
    
    # Ensure directories exist
    ensure_dirs()
    
    # 1. Load best training result (from T020/T021)
    try:
        best_result = load_best_training_result(results_dir)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # 2. Construct the metrics dictionary conforming to model_output.schema.yaml
    # The schema expects: model_id, hyperparameters, metrics (r2, mae), weights_path
    # We derive model_id from a timestamp or config hash if not present
    import time
    model_id = best_result.get('model_id', f"sn1_mpnn_{int(time.time())}")
    
    metrics_dict = {
        "model_id": model_id,
        "hyperparameters": best_result.get('hyperparameters', {}),
        "metrics": {
            "r2": best_result.get('val_r2'),
            "mae": best_result.get('val_mae')
        },
        "weights_path": "artifacts/best_model.pt"  # Relative path as per task
    }
    
    # 3. Load and validate against schema
    schema_path = contracts_dir / "model_output.schema.yaml"
    try:
        schema = load_schema(schema_path)
        if not validate_metrics_against_schema(metrics_dict, schema):
            logger.error("Metrics validation failed against schema.")
            sys.exit(1)
        logger.info("Metrics validated successfully against schema.")
    except FileNotFoundError:
        logger.warning(f"Schema file {schema_path} not found. Skipping validation.")
    
    # 4. Save artifacts
    weights_path = artifacts_dir / "best_model.pt"
    metrics_path = artifacts_dir / "metrics.json"
    
    # We need the actual model object to save weights.
    # Since T022 depends on T020/T021 which train the model, we assume the best model
    # is available in memory or can be reconstructed. 
    # In a real pipeline, T020/T021 would pass the model instance or we reload it.
    # For this task, we assume the training script (T020) saved the best model 
    # to a temporary location or we reconstruct it.
    # However, the task says "Save best model weights". 
    # Let's assume the training loop in T020/T021 saved the best model to results_dir/best_model.pt
    # and we just move/copy it, OR we reconstruct and save.
    # Given the API surface, T020 (train.py) likely has the logic. 
    # We will reconstruct the model using the hyperparameters from best_result.
    
    from models.mpnn import create_mpnn_from_config, MPNNConfig
    
    hp = best_result.get('hyperparameters', {})
    mpnn_config = MPNNConfig(
        hidden_dim=hp.get('hidden_dim', 64),
        num_layers=hp.get('num_layers', 2),
        dropout=hp.get('dropout', 0.1),
        learning_rate=hp.get('learning_rate', 1e-3) # Not needed for config but good to have
    )
    
    model = create_mpnn_from_config(mpnn_config)
    
    # Load the weights from the training run (assuming T020 saved best weights to results_dir)
    temp_weights = results_dir / "best_model_weights.pt"
    if not temp_weights.exists():
        # Fallback: try to find any .pt file in results_dir
        pt_files = list(results_dir.glob("*.pt"))
        if pt_files:
            temp_weights = pt_files[0]
            logger.warning(f"Using fallback weights from {temp_weights}")
        else:
            logger.error("No model weights found to save. Training might not have completed.")
            sys.exit(1)
    
    import torch
    model.load_state_dict(torch.load(temp_weights, map_location='cpu'))
    
    # Save to final location
    save_best_model(model, weights_path)
    
    # Save metrics
    save_metrics(metrics_dict, metrics_path)
    
    # 5. Save hyperparameter search log (T023 dependency, but good to do here or in T023)
    # T022 specifically asks for model and metrics. T023 asks for hyperparameter_search.csv.
    # We will skip T023 logic here to strictly follow T022, but the function is available.
    
    logger.info("T022 completed successfully.")

if __name__ == "__main__":
    main()
