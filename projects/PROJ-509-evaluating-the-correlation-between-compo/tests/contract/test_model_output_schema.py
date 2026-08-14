import pytest
import json
from pathlib import Path


def test_model_output_schema(tmp_path):
    """Test model output schema validation."""
    schema = {
        "required_keys": ["RandomForest", "GradientBoosting", "predictive_power"],
        "model_keys": ["r2", "mae", "rmse"],
    }

    metrics = {
        "RandomForest": {"r2": 0.5, "mae": 0.1, "rmse": 0.2},
        "GradientBoosting": {"r2": 0.6, "mae": 0.09, "rmse": 0.18},
        "predictive_power": True,
    }

    # Validate
    for key in schema["required_keys"]:
        assert key in metrics

    for model in ["RandomForest", "GradientBoosting"]:
        for metric in schema["model_keys"]:
            assert metric in metrics[model]