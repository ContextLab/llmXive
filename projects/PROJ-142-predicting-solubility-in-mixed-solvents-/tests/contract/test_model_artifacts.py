"""
Contract tests for model artifact validation.

This module validates the structure and content of model artifacts
produced by the training pipeline (T021/T022).
"""
import os
import json
import pickle
from pathlib import Path
from typing import Any, Dict

import pytest

# Import project constants for path resolution
# Note: We use a relative import path compatible with the project structure
try:
    from code.utils.constants import ARTIFACTS_DIR
except ImportError:
    # Fallback for direct execution if constants.py is not fully populated yet
    # In a real run, T004 (constants.py) should already exist.
    # If T004 is missing, we define a temporary fallback to allow the test to run.
    from pathlib import Path
    ARTIFACTS_DIR = Path("data/artifacts")


def _load_artifact(filename: str) -> Any:
    """Helper to load an artifact from the artifacts directory."""
    path = ARTIFACTS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Artifact not found: {path}")
    
    if filename.endswith('.pkl'):
        with open(path, 'rb') as f:
            return pickle.load(f)
    elif filename.endswith('.json'):
        with open(path, 'r') as f:
            return json.load(f)
    else:
        raise ValueError(f"Unsupported artifact type: {filename}")


def _validate_model_dict(model_data: Dict[str, Any]) -> bool:
    """
    Validates the internal structure of a loaded model dictionary.
    
    Expected schema:
    {
        "model_name": str,
        "model_object": object (unpickled),
        "metrics": {
            "rmse": float,
            "r2": float,
            "mae": float
        },
        "hyperparameters": dict,
        "training_metadata": {
            "seed": int,
            "timestamp": str
        }
    }
    """
    required_keys = ["model_name", "model_object", "metrics", "hyperparameters"]
    
    for key in required_keys:
        if key not in model_data:
            return False, f"Missing required key: {key}"
    
    if not isinstance(model_data["model_name"], str):
        return False, "model_name must be a string"
    
    if not isinstance(model_data["metrics"], dict):
        return False, "metrics must be a dictionary"
    
    metric_keys = ["rmse", "r2"]
    for m_key in metric_keys:
        if m_key not in model_data["metrics"]:
            return False, f"Missing metric: {m_key}"
        if not isinstance(model_data["metrics"][m_key], (int, float)):
            return False, f"Metric {m_key} must be numeric"
    
    if not isinstance(model_data["hyperparameters"], dict):
        return False, "hyperparameters must be a dictionary"
    
    return True, "Valid"


def test_model_artifact_valid():
    """
    Contract test: Verify that model artifacts exist and contain valid data.
    
    This test checks:
    1. The artifact file exists at the expected path.
    2. The file can be successfully deserialized (pickle/json).
    3. The deserialized object contains the required schema keys.
    4. Metrics are numeric and hyperparameters are present.
    
    Expected artifact path: data/artifacts/trained_models.pkl
    """
    artifact_path = ARTIFACTS_DIR / "trained_models.pkl"
    
    # Assert file existence
    assert artifact_path.exists(), f"Model artifact file not found at {artifact_path}"
    
    # Load the artifact
    try:
        with open(artifact_path, 'rb') as f:
            models = pickle.load(f)
    except Exception as e:
        pytest.fail(f"Failed to deserialize model artifact: {e}")
    
    # Handle both single model dict and list of models
    if isinstance(models, dict):
        models_list = [models]
    elif isinstance(models, list):
        models_list = models
    else:
        pytest.fail(f"Unexpected artifact structure: {type(models)}")
    
    assert len(models_list) > 0, "Model artifact list is empty"
    
    # Validate each model entry
    for i, model_data in enumerate(models_list):
        is_valid, message = _validate_model_dict(model_data)
        assert is_valid, f"Model entry {i} failed validation: {message}"
        
        # Additional check: ensure model_object is not None
        assert model_data["model_object"] is not None, \
            f"Model entry {i} has a None model_object"
    
    # If we reach here, the contract is satisfied
    assert True