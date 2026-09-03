import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Add project root to path to allow relative imports if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import get_env_var
from utils.io import setup_logging

# Configure logger
logger = logging.getLogger(__name__)

def ensure_models_dir() -> Path:
    """Ensure the code/models directory exists."""
    models_dir = PROJECT_ROOT / "code" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured models directory exists at: {models_dir}")
    return models_dir

def serialize_model(
    model: Any,
    model_type: str,
    hyperparameters: Dict[str, Any],
    cv_scores: Optional[Dict[str, Any]] = None,
    version: str = "v1"
) -> Tuple[Path, Path]:
    """
    Serialize a trained model to disk using Joblib (pickle) and save metadata.

    Args:
        model: The trained scikit-learn (or compatible) model instance.
        model_type: String identifier for the model (e.g., 'linear_regression', 'random_forest').
        hyperparameters: Dictionary of hyperparameters used for training.
        cv_scores: Optional dictionary of cross-validation scores (e.g., {'r2_mean': 0.85, 'mae_mean': 0.12}).
        version: Version string for the model file (default 'v1').

    Returns:
        Tuple of (model_path, metadata_path) as Path objects.

    Raises:
        FileNotFoundError: If the model object is None.
        ValueError: If model_type is invalid.
    """
    if model is None:
        raise FileNotFoundError("Cannot serialize a None model object.")

    if not model_type or not isinstance(model_type, str):
        raise ValueError("model_type must be a non-empty string.")

    models_dir = ensure_models_dir()

    # Construct filenames
    model_filename = f"{model_type}_{version}.pkl"
    meta_filename = f"{model_type}_{version}_meta.json"

    model_path = models_dir / model_filename
    meta_path = models_dir / meta_filename

    # Serialize model
    logger.info(f"Serializing {model_type} model to {model_path}")
    try:
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        logger.info(f"Model successfully saved to {model_path}")
    except Exception as e:
        logger.error(f"Failed to save model to {model_path}: {e}")
        raise

    # Prepare metadata
    metadata = {
        "model_type": model_type,
        "version": version,
        "hyperparameters": hyperparameters,
        "cv_scores": cv_scores if cv_scores else {},
        "serialization_path": str(model_path),
        "timestamp": None  # Can be filled by caller if needed, or left as None
    }

    # Serialize metadata
    logger.info(f"Saving metadata to {meta_path}")
    try:
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Metadata successfully saved to {meta_path}")
    except Exception as e:
        logger.error(f"Failed to save metadata to {meta_path}: {e}")
        # Attempt to clean up the model file if metadata fails
        if model_path.exists():
            model_path.unlink()
        raise

    return model_path, meta_path

def load_model(model_path: str) -> Any:
    """
    Load a model from a pickle file.

    Args:
        model_path: Path to the .pkl file.

    Returns:
        The loaded model object.

    Raises:
        FileNotFoundError: If the file does not exist.
        pickle.UnpicklingError: If the file is corrupted.
    """
    path = Path(model_path)
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    logger.info(f"Loading model from {model_path}")
    with open(path, 'rb') as f:
        model = pickle.load(f)
    return model

def load_latest_metadata(model_type: str, version: str = "v1") -> Dict[str, Any]:
    """
    Load metadata for a specific model version.

    Args:
        model_type: The type of model (e.g., 'linear_regression').
        version: The version string (e.g., 'v1').

    Returns:
        Dictionary containing metadata.

    Raises:
        FileNotFoundError: If the metadata file does not exist.
    """
    models_dir = ensure_models_dir()
    meta_filename = f"{model_type}_{version}_meta.json"
    meta_path = models_dir / meta_filename

    if not meta_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {meta_path}")

    logger.info(f"Loading metadata from {meta_path}")
    with open(meta_path, 'r') as f:
        metadata = json.load(f)
    return metadata

def main() -> None:
    """
    Main entry point for serialization task.
    This function is designed to be called by the training pipeline (T029)
    after a model has been trained and evaluated.
    
    For T031 implementation, this serves as the standalone runner if needed,
    but primarily it is called by train.py after training.
    """
    setup_logging()
    logger.info("Starting Model Serialization Task (T031)")

    # Example usage simulation (in real flow, this is called by train.py)
    # We will not instantiate a model here to avoid dependency on training logic,
    # but we ensure the functions are callable.
    
    # Verify directory creation
    try:
        ensure_models_dir()
        logger.info("Models directory verified.")
    except Exception as e:
        logger.error(f"Failed to ensure models directory: {e}")
        sys.exit(1)

    # Note: Actual serialization happens in train.py after training.
    # This script confirms the infrastructure is ready.
    logger.info("Model serialization infrastructure ready.")

if __name__ == "__main__":
    main()