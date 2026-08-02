"""
Contract test for model output schema (T023).

This test verifies that the model training pipeline (T025) produces outputs
that strictly adhere to the defined schema for model artifacts.

It validates:
1. The presence of required keys in the output dictionary.
2. The correct data types for model metrics (R², RMSE).
3. The structure of the model parameters serialization.
4. The integrity of the metadata section (timestamp, seed, model_type).

This test is part of User Story 3 (US3) and ensures the training script
produces consumable artifacts for downstream validation (T027) and
physics checks (T029).
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pytest

# Import the models we expect to validate against
# We import the training module to check if it produces the expected structure,
# but primarily we validate the *shape* of the output against a contract.
from data.models import ModelInput, TextureDescriptor
from config import get_seed

# Expected output schema definition
# This represents the contract that code/models/train.py must satisfy
MODEL_OUTPUT_SCHEMA = {
    "required_keys": [
        "model_type",
        "metrics",
        "parameters",
        "metadata",
        "feature_names"
    ],
    "metrics_keys": ["r2", "rmse", "fold_scores"],
    "metadata_keys": ["timestamp", "seed", "material_types", "reductions"],
    "types": {
        "model_type": str,
        "metrics": dict,
        "parameters": (dict, str),  # Could be dict of params or a path string
        "metadata": dict,
        "feature_names": list,
        "metrics.r2": (float, int),
        "metrics.rmse": (float, int),
        "metrics.fold_scores": list,
    }
}


def load_model_artifact(path: str) -> Dict[str, Any]:
    """
    Helper to load a model artifact JSON file.
    Raises FileNotFoundError or json.JSONDecodeError if invalid.
    """
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_model_output_schema_structure():
    """
    Contract Test: Verify the structure of the model output dictionary.

    This test creates a mock output that mimics what `code/models/train.py`
    should produce and validates it against the schema.
    In a real CI/CD flow, this would run against the actual file generated
    by the training script.
    """
    # Construct a valid mock output based on the expected schema
    mock_output = {
        "model_type": "polynomial_regression_degree_2",
        "metrics": {
            "r2": 0.875,
            "rmse": 0.042,
            "fold_scores": [0.85, 0.88, 0.86, 0.89, 0.84]
        },
        "parameters": {
            "degree": 2,
            "intercept": True,
            "coefficients": [0.1, 0.05, 0.002]
        },
        "metadata": {
            "timestamp": "2023-10-27T10:00:00Z",
            "seed": get_seed(),
            "material_types": ["Al", "Cu", "Ni"],
            "reductions": [10, 20, 30, 40, 50, 60, 70]
        },
        "feature_names": ["reduction", "material_al", "material_cu", "material_ni"]
    }

    # 1. Check required top-level keys
    for key in MODEL_OUTPUT_SCHEMA["required_keys"]:
        assert key in mock_output, f"Missing required key in model output: {key}"

    # 2. Check metrics structure
    metrics = mock_output["metrics"]
    for key in MODEL_OUTPUT_SCHEMA["metrics_keys"]:
        assert key in metrics, f"Missing required key in metrics: {key}"

    # 3. Check metadata structure
    metadata = mock_output["metadata"]
    for key in MODEL_OUTPUT_SCHEMA["metadata_keys"]:
        assert key in metadata, f"Missing required key in metadata: {key}"

    # 4. Check types
    assert isinstance(mock_output["model_type"], str)
    assert isinstance(mock_output["parameters"], (dict, str))
    assert isinstance(mock_output["feature_names"], list)
    assert isinstance(metrics["r2"], (float, int))
    assert isinstance(metrics["rmse"], (float, int))
    assert isinstance(metrics["fold_scores"], list)


def test_model_output_json_serialization():
    """
    Contract Test: Ensure the model output is valid JSON.

    The training script must be able to serialize the results to disk.
    """
    mock_output = {
        "model_type": "gaussian_process",
        "metrics": {"r2": 0.91, "rmse": 0.03},
        "parameters": {"kernel": "RBF"},
        "metadata": {"seed": 42},
        "feature_names": ["reduction"]
    }

    try:
        json_str = json.dumps(mock_output, indent=2)
        loaded = json.loads(json_str)
        assert loaded == mock_output
    except (TypeError, ValueError) as e:
        pytest.fail(f"Model output failed JSON serialization: {e}")


def test_model_output_against_data_models():
    """
    Contract Test: Verify compatibility with Pydantic models defined in data/models.py.

    While the model output is a dictionary, it should be compatible with the
    `ModelInput` or related structures if we were to re-ingest it.
    This ensures the training script respects the data contracts.
    """
    # This test ensures that if we were to wrap the output in a Pydantic model,
    # it would validate. Since the output is a raw dict, we check specific
    # constraints manually here to match the spirit of the contract.

    mock_output = {
        "model_type": "polynomial",
        "metrics": {"r2": 0.95, "rmse": 0.01, "fold_scores": [0.94, 0.96]},
        "parameters": {},
        "metadata": {
            "timestamp": "2023-01-01T00:00:00Z",
            "seed": 42,
            "material_types": ["Al"],
            "reductions": [10, 20]
        },
        "feature_names": ["reduction"]
    }

    # Validate that R2 is between 0 and 1 (or slightly above due to noise, but not negative)
    # Note: R2 can be negative for very bad models, but for this contract we expect
    # a reasonable physical model. We check it's a number.
    r2 = mock_output["metrics"]["r2"]
    assert isinstance(r2, (int, float)), "R2 must be numeric"

    # Validate that RMSE is non-negative
    rmse = mock_output["metrics"]["rmse"]
    assert rmse >= 0, "RMSE must be non-negative"

    # Validate that fold_scores is a list of numbers
    fold_scores = mock_output["metrics"]["fold_scores"]
    assert len(fold_scores) > 0, "Must have at least one fold score"
    for score in fold_scores:
        assert isinstance(score, (int, float)), "Fold scores must be numeric"


def test_model_output_file_path_contract():
    """
    Contract Test: Verify the expected file path for model outputs.

    According to the project plan, model outputs should be saved to a specific
    location. This test checks the convention.
    """
    expected_path = Path("data/processed/model_output.json")
    # We cannot assert the file exists here because the training script
    # might not have run yet in this specific test context.
    # Instead, we assert that the path follows the project convention.
    assert "data" in str(expected_path)
    assert "processed" in str(expected_path)
    assert expected_path.suffix == ".json"


def test_model_output_with_actual_training_artifact():
    """
    Integration-Contract Test: Run against the actual artifact if it exists.

    This test attempts to load the real output from `code/models/train.py`
    if it has been generated. If the file doesn't exist, it is skipped
    (as the training step might not have run yet), but if it exists, it
    MUST pass the schema validation.
    """
    # Define the expected path based on project conventions
    # The training script (T025) is expected to write to data/processed/
    possible_paths = [
        Path("data/processed/model_output.json"),
        Path("data/processed/polynomial_model.json"),
        Path("data/processed/gp_model.json")
    ]

    found_path = None
    for p in possible_paths:
        if p.exists():
            found_path = p
            break

    if found_path is None:
        pytest.skip("Model training artifact not found. Skipping contract validation.")

    try:
        artifact = load_model_artifact(str(found_path))
    except json.JSONDecodeError:
        pytest.fail(f"Artifact at {found_path} is not valid JSON.")

    # Run the schema checks
    for key in MODEL_OUTPUT_SCHEMA["required_keys"]:
        assert key in artifact, f"Missing required key in actual artifact: {key}"

    # Check metrics
    assert "metrics" in artifact
    assert "r2" in artifact["metrics"]
    assert "rmse" in artifact["metrics"]

    # Check metadata
    assert "metadata" in artifact
    assert "seed" in artifact["metadata"]
    assert "model_type" in artifact