import pytest
import json
import yaml
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from models.save_artifacts import (
    load_best_training_result,
    validate_metrics_against_schema,
    load_schema,
    save_metrics
)

@pytest.fixture
def temp_dirs():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        results_dir = tmp_path / "results"
        artifacts_dir = tmp_path / "artifacts"
        contracts_dir = tmp_path / "contracts"
        
        results_dir.mkdir()
        artifacts_dir.mkdir()
        contracts_dir.mkdir()
        
        yield {
            "results": results_dir,
            "artifacts": artifacts_dir,
            "contracts": contracts_dir
        }

def test_validate_metrics_against_schema_valid(temp_dirs):
    # Create a mock schema
    schema_content = {
        "required": ["model_id", "hyperparameters", "metrics", "weights_path"],
        "properties": {
            "metrics": {
                "required": ["r2", "mae"]
            }
        }
    }
    
    metrics = {
        "model_id": "test-123",
        "hyperparameters": {"lr": 0.01},
        "metrics": {"r2": 0.95, "mae": 0.1},
        "weights_path": "path/to/model.pt"
    }
    
    assert validate_metrics_against_schema(metrics, schema_content) is True

def test_validate_metrics_against_schema_missing_key(temp_dirs):
    schema_content = {"required": ["model_id"]}
    metrics = {
        "hyperparameters": {},
        "metrics": {"r2": 0.95, "mae": 0.1},
        "weights_path": "path.pt"
    }
    
    assert validate_metrics_against_schema(metrics, schema_content) is False

def test_validate_metrics_against_schema_missing_nested_metric(temp_dirs):
    schema_content = {"required": ["metrics"]}
    metrics = {
        "model_id": "test",
        "hyperparameters": {},
        "metrics": {"r2": 0.95}, # Missing mae
        "weights_path": "path.pt"
    }
    
    assert validate_metrics_against_schema(metrics, schema_content) is False

def test_load_schema(temp_dirs):
    schema_file = temp_dirs["contracts"] / "test_schema.yaml"
    schema_data = {"test": "value"}
    with open(schema_file, 'w') as f:
        yaml.dump(schema_data, f)
    
    loaded = load_schema(schema_file)
    assert loaded == schema_data

def test_load_schema_not_found(temp_dirs):
    with pytest.raises(FileNotFoundError):
        load_schema(temp_dirs["contracts"] / "nonexistent.yaml")

def test_save_metrics(temp_dirs):
    metrics = {
        "model_id": "test",
        "hyperparameters": {},
        "metrics": {"r2": 0.9, "mae": 0.1},
        "weights_path": "path.pt"
    }
    out_path = temp_dirs["artifacts"] / "test_metrics.json"
    
    save_metrics(metrics, out_path)
    
    assert out_path.exists()
    with open(out_path, 'r') as f:
        loaded = json.load(f)
    assert loaded == metrics