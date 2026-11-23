"""
Model Serialization Module (T031)

Implements model serialization to the code/models/ directory with metadata
including hyperparameters and cross-validation scores.

Artifacts produced:
- code/models/{model_type}_v1.pkl
- code/models/{model_type}_v1_meta.json
"""
import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.io import compute_sha256
from utils.config import get_env_var

logger = logging.getLogger(__name__)

def ensure_models_dir() -> Path:
    """Ensure the models directory exists."""
    models_dir = Path("code/models")
    models_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured models directory exists: {models_dir}")
    return models_dir

def serialize_model(
    model: Any,
    model_type: str,
    hyperparameters: Dict[str, Any],
    cv_scores: Optional[Dict[str, Any]] = None,
    version: str = "v1"
) -> Dict[str, str]:
    """
    Serialize a trained model and its metadata to the code/models/ directory.

    Args:
        model: The trained sklearn model instance.
        model_type: Type of model (e.g., 'linear_regression', 'random_forest').
        hyperparameters: Dictionary of model hyperparameters.
        cv_scores: Optional dictionary of cross-validation scores (e.g., {'r2_mean': 0.85, 'mae_mean': 0.02}).
        version: Version string for the model files (default: 'v1').

    Returns:
        Dictionary with paths to the saved model and metadata files.
    """
    models_dir = ensure_models_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Define file paths
    model_filename = f"{model_type}_{version}.pkl"
    meta_filename = f"{model_type}_{version}_meta.json"

    model_path = models_dir / model_filename
    meta_path = models_dir / meta_filename

    # Serialize model
    try:
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        logger.info(f"Model saved to: {model_path}")
    except Exception as e:
        logger.error(f"Failed to serialize model: {e}")
        raise

    # Prepare metadata
    metadata = {
        "model_type": model_type,
        "version": version,
        "serialized_at": timestamp,
        "hyperparameters": hyperparameters,
        "cv_scores": cv_scores or {},
        "model_file": model_filename,
        "checksum_sha256": compute_sha256(str(model_path))
    }

    # Save metadata
    try:
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Metadata saved to: {meta_path}")
    except Exception as e:
        logger.error(f"Failed to save metadata: {e}")
        # Clean up model file if metadata fails
        if model_path.exists():
            model_path.unlink()
        raise

    return {
        "model_path": str(model_path),
        "meta_path": str(meta_path)
    }

def load_model(model_path: str) -> Any:
    """
    Load a serialized model from disk.

    Args:
        model_path: Path to the .pkl file.

    Returns:
        The loaded model object.
    """
    path = Path(model_path)
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {path}")

    try:
        with open(path, 'rb') as f:
            model = pickle.load(f)
        logger.info(f"Model loaded from: {path}")
        return model
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def load_latest_metadata(model_type: str, models_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the metadata for the latest version of a specific model type.

    Args:
        model_type: Type of model to search for.
        models_dir: Optional path to models directory (defaults to code/models).

    Returns:
        Dictionary containing the metadata.
    """
    if models_dir is None:
        models_dir = Path("code/models")

    pattern = f"{model_type}_*_meta.json"
    meta_files = list(models_dir.glob(pattern))

    if not meta_files:
        raise FileNotFoundError(f"No metadata files found for model type: {model_type}")

    # Sort by modification time to get the latest
    latest_file = max(meta_files, key=lambda p: p.stat().st_mtime)

    with open(latest_file, 'r') as f:
        metadata = json.load(f)

    logger.info(f"Loaded latest metadata from: {latest_file}")
    return metadata

def main() -> None:
    """
    Main entry point for T031: Model Serialization.

    This function demonstrates the serialization process by:
    1. Loading a trained model (simulated or loaded from previous step).
    2. Extracting hyperparameters and CV scores.
    3. Serializing the model and metadata to code/models/.
    """
    setup_logging = False
    try:
        from utils.io import setup_logging
        setup_logging()
    except ImportError:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    logger.info("Starting Model Serialization (T031)...")

    # Example usage:
    # In a real pipeline, 'model', 'hyperparameters', and 'cv_scores'
    # would come from the training step (T028/T029).
    # Here we demonstrate the function calls with placeholders
    # that would be replaced by actual objects in the pipeline.

    # Mock data for demonstration (In real execution, these come from train.py)
    # We assume a scenario where training has just finished.
    
    # Since we cannot import the trained model directly without running the training,
    # we will structure this as a utility that the training script calls,
    # or a standalone script that loads the model from a temporary location if needed.
    # However, per T031 requirement, we must produce the artifacts.
    
    # To ensure the script is runnable and produces the artifact as requested:
    # We will check if a model exists from previous steps (e.g. from a pickle passed via args or env),
    # or if this is a standalone run, we will simulate the serialization of a dummy model 
    # to prove the pipeline works, BUT the task requires REAL output from the pipeline.
    
    # Correct approach for T031 in the pipeline:
    # This script is meant to be called by train.py OR train.py calls the serialize_model function.
    # Since T029 (Random Forest) and T028 (Linear Regression) are completed, 
    # we assume they call this function or we call it here if invoked directly.
    
    # To satisfy the "produce real output" constraint:
    # We will look for the trained model files produced by T029/T028 if they exist in a temp location,
    # OR we assume this script is the entry point that the user runs after training.
    # Given the constraints, we will implement the logic to serialize a model passed as an argument
    # or load a model from a known path if provided.
    
    # For the purpose of this task implementation, we will assume the training script 
    # passes the model object to this function. 
    # However, to make this a standalone runnable script that generates the artifact:
    # We will check if we can load a model from a specific path (e.g. data/processed/temp_model.pkl)
    # or if not, we will raise an error indicating the model must be provided by the training step.
    
    # Actually, the most robust way for T031 is to be a function called by T029/T028.
    # But if run as `python code/modeling/serialize.py`, it should demonstrate the capability.
    # We will create a minimal dummy model to serialize if no real model is found, 
    # BUT the prompt says "Produce real outputs, not demos".
    # Therefore, this script should ideally be invoked by the training script.
    # We will implement the logic to serialize a model if provided via command line or env.
    
    # Let's assume the training script (T029) saves the model to a temp location and calls this,
    # or we simply expose the function.
    # To ensure the artifact exists, we will assume the training pipeline has run and 
    # we are re-serializing or this is the final step.
    
    # Since we cannot guarantee the training step has run in this isolated execution,
    # and we must produce the artifact, we will implement the logic to:
    # 1. Check for a model file passed via environment variable MODEL_PATH.
    # 2. If found, serialize it.
    # 3. If not found, log a warning that this script is intended to be called by the training script.
    
    # However, to strictly satisfy "Produce real outputs", we must have a model.
    # We will assume the training script (T029) has saved a model to a known location 
    # or we will simulate the serialization of a sklearn model instance.
    # Wait, the prompt says "If a script whose entry point only prints a demo... is INCOMPLETE".
    # So we must NOT create a dummy model.
    
    # Strategy: This script is designed to be imported by train.py (T029) to serialize the model.
    # If run directly, it will check for a model path in env vars.
    # If no model is found, it exits with a clear error message.
    # This ensures no fake data is produced.
    
    model_path_env = get_env_var("MODEL_PATH_TO_SERIALIZE", default=None)
    
    if model_path_env:
        model_path = Path(model_path_env)
        if not model_path.exists():
            logger.error(f"Model file not found at {model_path}. Cannot serialize.")
            sys.exit(1)
        
        # Load the model
        model = load_model(str(model_path))
        
        # We need hyperparameters and cv_scores. These should be passed via env or a JSON file.
        # For simplicity, we assume they are in a JSON file next to the model or passed via env.
        meta_json_path = get_env_var("MODEL_META_JSON_PATH", default=None)
        if meta_json_path and Path(meta_json_path).exists():
            with open(meta_json_path, 'r') as f:
                meta_data = json.load(f)
            hyperparameters = meta_data.get("hyperparameters", {})
            cv_scores = meta_data.get("cv_scores", {})
            model_type = meta_data.get("model_type", "unknown")
        else:
            # Fallback: Try to infer from model class or raise error
            model_type = model.__class__.__name__.lower()
            hyperparameters = getattr(model, 'get_params', lambda: {})()
            cv_scores = {}
            logger.warning(f"Metadata JSON not found. Using model introspection for {model_type}.")

        # Serialize
        result = serialize_model(
            model=model,
            model_type=model_type,
            hyperparameters=hyperparameters,
            cv_scores=cv_scores
        )
        
        logger.info(f"Serialization complete. Model: {result['model_path']}, Meta: {result['meta_path']}")
        sys.exit(0)
    else:
        logger.error("No model path provided. This script is intended to be called by the training pipeline.")
        logger.error("Set MODEL_PATH_TO_SERIALIZE environment variable to the path of the trained model.")
        sys.exit(1)

if __name__ == "__main__":
    main()