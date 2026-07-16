import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from models.save_artifacts import load_best_training_result, validate_metrics_against_schema, save_metrics

def test_load_best_training_result():
    """Test loading the best training result from a JSON file."""
    # Create a temporary results file
    results_data = [
        {"val_r2": 0.5, "val_mae": 0.2, "config": {"lr": 0.01}},
        {"val_r2": 0.8, "val_mae": 0.1, "config": {"lr": 0.001}}
    ]
    results_path = Path("test_results.json")
    with open(results_path, 'w') as f:
        json.dump(results_data, f)

    result = load_best_training_result(results_path)
    assert result is not None
    assert result['val_r2'] == 0.8
    assert result['config']['lr'] == 0.001

    # Clean up
    os.remove(results_path)

def test_validate_metrics_against_schema():
    """Test validation of metrics against schema."""
    valid_metrics = {
        "model_id": "test_model",
        "hyperparameters": {"lr": 0.01},
        "metrics": {"r2": 0.9, "mae": 0.1},
        "weights_path": "artifacts/best_model.pt"
    }
    assert validate_metrics_against_schema(valid_metrics) is True

    invalid_metrics = {
        "model_id": "test_model",
        "hyperparameters": {"lr": 0.01},
        "metrics": {"r2": 0.9},  # Missing 'mae'
        "weights_path": "artifacts/best_model.pt"
    }
    assert validate_metrics_against_schema(invalid_metrics) is False

    invalid_metrics = {
        "model_id": "test_model",
        "hyperparameters": {"lr": 0.01},
        "metrics": {"r2": 0.9, "mae": 0.1},
        # Missing 'weights_path'
    }
    assert validate_metrics_against_schema(invalid_metrics) is False

def test_save_metrics():
    """Test saving metrics to a JSON file."""
    metrics = {
        "model_id": "test_model",
        "hyperparameters": {"lr": 0.01},
        "metrics": {"r2": 0.9, "mae": 0.1},
        "weights_path": "artifacts/best_model.pt"
    }
    output_path = Path("test_metrics.json")
    assert save_metrics(metrics, output_path) is True
    assert output_path.exists()

    # Clean up
    os.remove(output_path)