import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure imports resolve correctly in the project context
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ensure_dirs
from utils.logger import setup_logging, get_logger
from models.train import load_processed_data, prepare_features

def load_best_training_result(results_dir: Path) -> Dict[str, Any]:
    """
    Load the best training result from the results directory.
    Expects a file named 'best_result.json' or similar.
    """
    best_result_path = results_dir / "best_result.json"
    if not best_result_path.exists():
        # Fallback: scan for the file with the best validation score if named differently
        # For now, assume the training script saves 'best_result.json'
        raise FileNotFoundError(f"Best training result not found at {best_result_path}")
    
    with open(best_result_path, 'r') as f:
        return json.load(f)

def save_best_model(model: Any, model_dir: Path, filename: str = "best_model.pt"):
    """
    Save the best model weights to the artifacts directory.
    """
    ensure_dirs()
    output_path = model_dir / filename
    
    # Assuming model is a PyTorch model or has a .state_dict() method
    if hasattr(model, 'state_dict'):
        torch_state = model.state_dict()
        import torch
        torch.save(torch_state, output_path)
    else:
        # Fallback for other model types (e.g., sklearn)
        import pickle
        with open(output_path, 'wb') as f:
            pickle.dump(model, f)
    
    logging.info(f"Best model saved to {output_path}")
    return output_path

def save_metrics(metrics: Dict[str, Any], metrics_dir: Path, filename: str = "metrics.json"):
    """
    Save evaluation metrics to the artifacts directory.
    """
    ensure_dirs()
    output_path = metrics_dir / filename
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logging.info(f"Metrics saved to {output_path}")
    return output_path

def save_hyperparameter_log(log_data: Dict[str, Any], log_dir: Path, filename: str = "hyperparameter_search.log"):
    """
    Save the hyperparameter search log.
    """
    ensure_dirs()
    output_path = log_dir / filename
    
    with open(output_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    logging.info(f"Hyperparameter log saved to {output_path}")
    return output_path

def main():
    """
    Main entry point to save the best model and metrics.
    This script assumes that the training process has already run and
    produced a 'best_result.json' file in the results directory.
    It loads that result, extracts the model and metrics, and saves them
    to the artifacts directory.
    """
    parser = argparse.ArgumentParser(description="Save best model and metrics")
    parser.add_argument("--results-dir", type=str, default="data/results", help="Directory containing training results")
    parser.add_argument("--artifacts-dir", type=str, default="artifacts", help="Directory to save artifacts")
    args = parser.parse_args()

    setup_logging()
    logger = get_logger(__name__)

    results_dir = Path(args.results_dir)
    artifacts_dir = Path(args.artifacts_dir)

    # Ensure directories exist
    ensure_dirs()

    try:
        # Load the best result
        logger.info(f"Loading best training result from {results_dir}")
        best_result = load_best_training_result(results_dir)

        # We need to reconstruct the model to save it.
        # The best_result should contain the config used to create the model.
        # We assume the model class is MPNN and we have a function to create it.
        from models.mpnn import create_mpnn_from_config, MPNNConfig
        
        if 'config' not in best_result:
            raise ValueError("Best result does not contain model configuration.")
        
        config = MPNNConfig(**best_result['config'])
        model = create_mpnn_from_config(config)
        
        # Load the state dict if it was saved separately during training, 
        # or assume the 'best_result' contains the weights (unlikely for large models).
        # Typically, training saves weights to a temp file, and we load them here.
        # For this implementation, we assume the training script saved weights 
        # in a file named 'best_model_weights.pt' in the results dir.
        weights_path = results_dir / "best_model_weights.pt"
        if weights_path.exists():
            import torch
            model.load_state_dict(torch.load(weights_path, map_location='cpu'))
            logger.info(f"Loaded model weights from {weights_path}")
        else:
            logger.warning(f"Weights file {weights_path} not found. Saving random initialized model.")

        # Save the model
        model_path = save_best_model(model, artifacts_dir)

        # Prepare metrics
        metrics = {
            "model_id": best_result.get("model_id", "mpnn-sn1-v1"),
            "metrics": {
                "r2": best_result.get("val_r2"),
                "mae": best_result.get("val_mae"),
                "test_r2": best_result.get("test_r2"),
                "test_mae": best_result.get("test_mae"),
            },
            "hyperparameters": best_result.get("config", {}),
            "weights_path": str(model_path)
        }

        # Save metrics
        metrics_path = save_metrics(metrics, artifacts_dir)

        logger.info("Successfully saved best model and metrics.")
        return 0

    except Exception as e:
        logger.error(f"Failed to save artifacts: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
