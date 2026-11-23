"""
Contract tests for validating schema definitions against generated data.
Ensures that training configurations and evaluation results conform to the
expected JSON Schema standards defined in the specs directory.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any

import pytest
import jsonschema
from jsonschema import validate, ValidationError

# Add project root to path if running directly
if "code" not in sys.path:
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

# Load schemas
SCHEMAS_DIR = Path(__file__).parent.parent.parent / "specs" / "001-dream-state-learning-implementing-rem-li"

@pytest.fixture
def training_schema() -> Dict[str, Any]:
    schema_path = SCHEMAS_DIR / "training_config.schema.yaml"
    if not schema_path.exists():
        pytest.fail(f"Schema file not found: {schema_path}")
    # Note: In a real CI environment, we might need to parse YAML if the file is .yaml
    # For this test, we assume the schema is loaded as JSON or we use a yaml loader
    # Since jsonschema expects a dict, we load the content.
    # We will use a simple approach: read the file and assume it's valid JSON/YAML structure
    # For robustness, we try to load as YAML if PyYAML is available, else JSON
    try:
        import yaml
        with open(schema_path, 'r') as f:
            return yaml.safe_load(f)
    except ImportError:
        # Fallback if yaml not installed, though requirements.txt should have it
        # or we parse manually if strictly JSON-like (but this file is YAML)
        # Given the constraints, we assume PyYAML is present as per T002 (scipy, etc usually bring yaml)
        # If not, we raise a clear error
        raise RuntimeError("PyYAML is required to load schema files. Install it via pip.")

@pytest.fixture
def evaluation_schema() -> Dict[str, Any]:
    schema_path = SCHEMAS_DIR / "evaluation_result.schema.yaml"
    if not schema_path.exists():
        pytest.fail(f"Schema file not found: {schema_path}")
    try:
        import yaml
        with open(schema_path, 'r') as f:
            return yaml.safe_load(f)
    except ImportError:
        raise RuntimeError("PyYAML is required to load schema files.")

@pytest.fixture
def valid_training_config() -> Dict[str, Any]:
    """Returns a minimal valid training configuration."""
    return {
        "model_name": "distilbert-base-uncased",
        "dataset_config": {
            "source": "glue",
            "subset": "sst2",
            "split": "train",
            "max_length": 128
        },
        "training_params": {
            "learning_rate": 5e-5,
            "batch_size": 8,
            "num_epochs": 2,
            "seed": 42,
            "warmup_steps": 10
        },
        "dream_params": {
            "ratio": 0.25,
            "mask_rate": 0.15,
            "entropy_threshold": 0.5,
            "max_retries": 3
        },
        "resource_limits": {
            "max_memory_gb": 7.0,
            "max_wall_clock_hours": 5.0
        }
    }

@pytest.fixture
def valid_evaluation_result() -> Dict[str, Any]:
    """Returns a minimal valid evaluation result."""
    return {
        "experiment_id": "exp-001-test",
        "timestamp": "2026-06-30T12:00:00Z",
        "model_info": {
            "name": "distilbert-base-uncased",
            "parameters": 66000000,
            "precision": "float32"
        },
        "dataset_info": {
            "source": "glue",
            "subset": "sst2",
            "split": "validation",
            "samples_evaluated": 100
        },
        "metrics": {
            "accuracy": 0.85,
            "loss": 0.45,
            "dream_phase_stats": {
                "total_dream_steps": 50,
                "avg_entropy": 1.2,
                "low_entropy_retries": 2
            }
        },
        "timing": {
            "total_wall_clock_seconds": 3600.5,
            "wake_phase_seconds": 2700.0,
            "dream_phase_seconds": 900.5
        }
    }

class TestTrainingConfigSchema:
    def test_valid_config(self, training_schema, valid_training_config):
        """Test that a valid config passes validation."""
        validate(instance=valid_training_config, schema=training_schema)

    def test_missing_required_field(self, training_schema, valid_training_config):
        """Test that missing a required field raises ValidationError."""
        config = valid_training_config.copy()
        del config["model_name"]
        with pytest.raises(ValidationError):
            validate(instance=config, schema=training_schema)

    def test_invalid_enum_value(self, training_schema, valid_training_config):
        """Test that an invalid enum value raises ValidationError."""
        config = valid_training_config.copy()
        config["dataset_config"]["source"] = "invalid_source"
        with pytest.raises(ValidationError):
            validate(instance=config, schema=training_schema)

    def test_invalid_type(self, training_schema, valid_training_config):
        """Test that an invalid type raises ValidationError."""
        config = valid_training_config.copy()
        config["training_params"]["learning_rate"] = "not_a_number"
        with pytest.raises(ValidationError):
            validate(instance=config, schema=training_schema)

class TestEvaluationResultSchema:
    def test_valid_result(self, evaluation_schema, valid_evaluation_result):
        """Test that a valid result passes validation."""
        validate(instance=valid_evaluation_result, schema=evaluation_schema)

    def test_missing_required_field(self, evaluation_schema, valid_evaluation_result):
        """Test that missing a required field raises ValidationError."""
        result = valid_evaluation_result.copy()
        del result["experiment_id"]
        with pytest.raises(ValidationError):
            validate(instance=result, schema=evaluation_schema)

    def test_invalid_timestamp_format(self, evaluation_schema, valid_evaluation_result):
        """Test that an invalid timestamp format raises ValidationError."""
        result = valid_evaluation_result.copy()
        result["timestamp"] = "not-a-date"
        with pytest.raises(ValidationError):
            validate(instance=result, schema=evaluation_schema)

    def test_missing_baseline_comparison(self, evaluation_schema, valid_evaluation_result):
        """Test that missing optional fields is allowed."""
        result = valid_evaluation_result.copy()
        # baseline_comparison is optional, so this should pass
        validate(instance=result, schema=evaluation_schema)

class TestSchemaFilesExist:
    def test_training_schema_exists(self):
        assert (SCHEMAS_DIR / "training_config.schema.yaml").exists()

    def test_evaluation_schema_exists(self):
        assert (SCHEMAS_DIR / "evaluation_result.schema.yaml").exists()
