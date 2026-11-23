import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import yaml

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.save_artifacts import (
    load_best_training_result,
    load_schema,
    validate_metrics_against_schema,
    save_best_model,
    save_metrics,
    main
)

@pytest.fixture
def temp_dirs():
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_schema():
    return {
        "required": ["model_id", "hyperparameters", "metrics", "weights_path"],
        "properties": {
            "metrics": {
                "required": ["r2", "mae"]
            }
        }
    }

@pytest.fixture
def sample_metrics():
    return {
        "model_id": "test-model-1",
        "hyperparameters": {"lr": 0.01, "layers": 2},
        "metrics": {"r2": 0.85, "mae": 0.12},
        "weights_path": "path/to/model.pt"
    }

def test_validate_metrics_success(sample_metrics, sample_schema):
    assert validate_metrics_against_schema(sample_metrics, sample_schema) is True

def test_validate_metrics_missing_key(sample_schema):
    bad_metrics = {
        "model_id": "test",
        "hyperparameters": {},
        # missing metrics
        "weights_path": "path"
    }
    assert validate_metrics_against_schema(bad_metrics, sample_schema) is False

def test_validate_metrics_missing_nested_key(sample_schema):
    bad_metrics = {
        "model_id": "test",
        "hyperparameters": {},
        "metrics": {"r2": 0.8}, # missing mae
        "weights_path": "path"
    }
    assert validate_metrics_against_schema(bad_metrics, sample_schema) is False

def test_save_metrics(temp_dirs):
    metrics = {
        "model_id": "test",
        "hyperparameters": {},
        "metrics": {"r2": 0.9, "mae": 0.1},
        "weights_path": "path"
    }
    output_path = temp_dirs / "metrics.json"
    save_metrics(metrics, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        loaded = json.load(f)
    assert loaded == metrics

def test_load_schema(temp_dirs):
    schema_path = temp_dirs / "schema.yaml"
    schema_data = {"test": "value"}
    with open(schema_path, 'w') as f:
        yaml.dump(schema_data, f)
    
    loaded = load_schema(schema_path)
    assert loaded == schema_data

def test_load_schema_not_found():
    with pytest.raises(FileNotFoundError):
        load_schema(Path("/nonexistent/schema.yaml"))