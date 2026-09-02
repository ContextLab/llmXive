"""
Contract test for model artifact schema (T020).

Validates that model artifacts produced by the training pipeline (T022, T023, T024)
conform to the expected schema defined in the project specifications.

This test ensures:
1. Required top-level keys are present (model_type, metrics, hyperparameters, timestamp, version).
2. Metrics dictionary contains required fields (r2, mae, duration_seconds, peak_memory_mb).
3. Hyperparameters are a non-empty dictionary.
4. Timestamp is a valid ISO format string.
5. Model type matches expected values ('baseline' or 'gnn').
"""

import json
import os
from datetime import datetime
from pathlib import Path

import pytest

# Expected artifact paths relative to project root
BASELINE_ARTIFACT_PATH = "data/models/baseline_model.json"
GNN_ARTIFACT_PATH = "data/models/gnn_model.json"
TRAINING_METRICS_PATH = "data/derived/training_metrics.json"

REQUIRED_TOP_LEVEL_KEYS = {
    "model_type",
    "metrics",
    "hyperparameters",
    "timestamp",
    "version"
}

REQUIRED_METRIC_KEYS = {
    "r2",
    "mae",
    "duration_seconds",
    "peak_memory_mb"
}

VALID_MODEL_TYPES = {"baseline", "gnn"}


def load_artifact(path: str) -> dict:
    """Load a JSON artifact from the given path."""
    full_path = Path(path)
    if not full_path.exists():
        raise FileNotFoundError(f"Artifact not found: {full_path}")
    
    with open(full_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_schema(artifact: dict, model_type: str) -> None:
    """
    Validate the schema of a model artifact.
    
    Args:
        artifact: The loaded JSON dictionary.
        model_type: The expected model type ('baseline' or 'gnn').
    
    Raises:
        AssertionError: If the schema validation fails.
    """
    # Check top-level keys
    missing_keys = REQUIRED_TOP_LEVEL_KEYS - set(artifact.keys())
    assert not missing_keys, f"Missing top-level keys: {missing_keys}"

    # Validate model_type
    assert artifact["model_type"] in VALID_MODEL_TYPES, \
        f"Invalid model_type: {artifact['model_type']}. Expected one of {VALID_MODEL_TYPES}."
    
    if model_type:
        assert artifact["model_type"] == model_type, \
            f"Model type mismatch. Expected {model_type}, got {artifact['model_type']}."

    # Validate metrics structure
    metrics = artifact["metrics"]
    assert isinstance(metrics, dict), "Metrics must be a dictionary."
    missing_metric_keys = REQUIRED_METRIC_KEYS - set(metrics.keys())
    assert not missing_metric_keys, f"Missing metric keys: {missing_metric_keys}"

    # Validate metric values are numeric
    for key in REQUIRED_METRIC_KEYS:
        val = metrics[key]
        assert isinstance(val, (int, float)), \
            f"Metric '{key}' must be numeric, got {type(val)}."
        
        # Basic sanity checks for metrics
        if key in ["r2"]:
            # R2 can be negative, but usually > -1 for reasonable models
            assert val > -10, f"R2 value {val} seems unreasonably low."
        if key in ["mae", "duration_seconds", "peak_memory_mb"]:
            assert val >= 0, f"Metric '{key}' must be non-negative, got {val}."

    # Validate hyperparameters
    hp = artifact["hyperparameters"]
    assert isinstance(hp, dict), "Hyperparameters must be a dictionary."
    assert len(hp) > 0, "Hyperparameters dictionary cannot be empty."

    # Validate timestamp
    timestamp_str = artifact["timestamp"]
    try:
        # Try parsing ISO format
        datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    except ValueError:
        raise AssertionError(f"Invalid timestamp format: {timestamp_str}")

    # Validate version
    version = artifact["version"]
    assert isinstance(version, str) and len(version) > 0, \
        "Version must be a non-empty string."


class TestBaselineModelArtifact:
    """Tests for the baseline model artifact schema."""

    def test_baseline_artifact_exists(self):
        """Check if the baseline artifact file exists."""
        assert Path(BASELINE_ARTIFACT_PATH).exists(), \
            f"Baseline model artifact not found at {BASELINE_ARTIFACT_PATH}"

    def test_baseline_schema_validity(self):
        """Validate the schema of the baseline model artifact."""
        artifact = load_artifact(BASELINE_ARTIFACT_PATH)
        validate_schema(artifact, model_type="baseline")


class TestGNNModelArtifact:
    """Tests for the GNN model artifact schema."""

    def test_gnn_artifact_exists(self):
        """Check if the GNN artifact file exists."""
        assert Path(GNN_ARTIFACT_PATH).exists(), \
            f"GNN model artifact not found at {GNN_ARTIFACT_PATH}"

    def test_gnn_schema_validity(self):
        """Validate the schema of the GNN model artifact."""
        artifact = load_artifact(GNN_ARTIFACT_PATH)
        validate_schema(artifact, model_type="gnn")


class TestTrainingMetricsArtifact:
    """Tests for the training metrics artifact schema."""

    def test_training_metrics_exists(self):
        """Check if the training metrics file exists."""
        assert Path(TRAINING_METRICS_PATH).exists(), \
            f"Training metrics artifact not found at {TRAINING_METRICS_PATH}"

    def test_training_metrics_schema(self):
        """Validate the schema of the training metrics artifact."""
        artifact = load_artifact(TRAINING_METRICS_PATH)
        
        required_keys = {"duration_seconds", "peak_memory_mb"}
        missing = required_keys - set(artifact.keys())
        assert not missing, f"Training metrics missing keys: {missing}"

        for key in required_keys:
            val = artifact[key]
            assert isinstance(val, (int, float)), \
                f"Training metric '{key}' must be numeric, got {type(val)}."
            assert val >= 0, f"Training metric '{key}' must be non-negative."