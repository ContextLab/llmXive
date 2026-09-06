"""
Contract tests for schema validation of training and evaluation artifacts.
Ensures that generated configuration and result files adhere to the defined JSON schemas.
"""
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any

import pytest
from jsonschema import validate, ValidationError, Draft7Validator

# Import the schema files directly if possible, or load them from disk
# Assuming schemas are stored in data/raw/ as per project structure
SCHEMA_DIR = Path(__file__).parent.parent.parent / "data" / "raw"

TRAINING_CONFIG_SCHEMA_PATH = SCHEMA_DIR / "training_config.schema.yaml"
EVALUATION_RESULT_SCHEMA_PATH = SCHEMA_DIR / "evaluation_result.schema.yaml"

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a JSON or YAML schema from disk."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        if schema_path.suffix in [".yaml", ".yml"]:
            if not HAS_YAML:
                pytest.skip("PyYAML not installed")
            return yaml.safe_load(f)
        else:
            return json.load(f)


@pytest.fixture
def training_config_schema():
    return load_schema(TRAINING_CONFIG_SCHEMA_PATH)


@pytest.fixture
def evaluation_result_schema():
    return load_schema(EVALUATION_RESULT_SCHEMA_PATH)


class TestTrainingConfigSchema:
    """Tests for the training_config.schema.yaml"""

    def test_valid_training_config(self, training_config_schema):
        """Test a valid training configuration passes validation."""
        valid_config = {
            "model_name": "distilbert-base-uncased",
            "dataset_name": "glue/sst2",
            "hyperparameters": {
                "learning_rate": 2e-5,
                "batch_size": 16,
                "warmup_steps": 10,
                "max_steps": 100,
                "entropy_threshold": 0.5
            },
            "dream_schedule": {
                "ratio": 4,
                "temperature": 0.7
            },
            "paths": {
                "output_dir": "data/results",
                "data_dir": "data/raw"
            }
        }
        validate(instance=valid_config, schema=training_config_schema)

    def test_missing_required_field(self, training_config_schema):
        """Test that missing required fields raise ValidationError."""
        invalid_config = {
            "model_name": "distilbert-base-uncased",
            # Missing dataset_name and hyperparameters
        }
        with pytest.raises(ValidationError):
            validate(instance=invalid_config, schema=training_config_schema)

    def test_invalid_type(self, training_config_schema):
        """Test that invalid types raise ValidationError."""
        invalid_config = {
            "model_name": "distilbert-base-uncased",
            "dataset_name": "glue/sst2",
            "hyperparameters": {
                "learning_rate": "not_a_number",  # Should be number
                "batch_size": 16,
                "warmup_steps": 10,
                "max_steps": 100,
                "entropy_threshold": 0.5
            },
            "dream_schedule": {
                "ratio": 4,
                "temperature": 0.7
            }
        }
        with pytest.raises(ValidationError):
            validate(instance=invalid_config, schema=training_config_schema)

    def test_negative_values(self, training_config_schema):
        """Test that negative values for positive-only fields raise ValidationError."""
        invalid_config = {
            "model_name": "distilbert-base-uncased",
            "dataset_name": "glue/sst2",
            "hyperparameters": {
                "learning_rate": -1e-5,  # Negative learning rate
                "batch_size": 16,
                "warmup_steps": 10,
                "max_steps": 100,
                "entropy_threshold": 0.5
            },
            "dream_schedule": {
                "ratio": 4,
                "temperature": 0.7
            }
        }
        with pytest.raises(ValidationError):
            validate(instance=invalid_config, schema=training_config_schema)


class TestEvaluationResultSchema:
    """Tests for the evaluation_result.schema.yaml"""

    def test_valid_evaluation_result(self, evaluation_result_schema):
        """Test a valid evaluation result passes validation."""
        valid_result = {
            "experiment_id": "exp-001",
            "model_name": "distilbert-base-uncased",
            "dataset_name": "glue/sst2",
            "metrics": {
                "accuracy": 0.85,
                "loss": 0.32,
                "entropy_mean": 0.45,
                "precision": 0.84,
                "recall": 0.86,
                "f1_score": 0.85
            },
            "stats": {
                "total_steps": 100,
                "dream_steps": 25,
                "wake_steps": 75
            },
            "timestamp": "2023-10-27T10:00:00Z",
            "config_snapshot": {}
        }
        validate(instance=valid_result, schema=evaluation_result_schema)

    def test_missing_required_field(self, evaluation_result_schema):
        """Test that missing required fields raise ValidationError."""
        invalid_result = {
            "experiment_id": "exp-001",
            # Missing model_name, dataset_name, metrics, timestamp
        }
        with pytest.raises(ValidationError):
            validate(instance=invalid_result, schema=evaluation_result_schema)

    def test_invalid_metric_range(self, evaluation_result_schema):
        """Test that metrics outside [0, 1] raise ValidationError."""
        invalid_result = {
            "experiment_id": "exp-001",
            "model_name": "distilbert-base-uncased",
            "dataset_name": "glue/sst2",
            "metrics": {
                "accuracy": 1.5,  # > 1.0
                "loss": 0.32,
                "entropy_mean": 0.45
            },
            "timestamp": "2023-10-27T10:00:00Z"
        }
        with pytest.raises(ValidationError):
            validate(instance=invalid_result, schema=evaluation_result_schema)

    def test_invalid_timestamp_format(self, evaluation_result_schema):
        """Test that invalid timestamp format raises ValidationError."""
        invalid_result = {
            "experiment_id": "exp-001",
            "model_name": "distilbert-base-uncased",
            "dataset_name": "glue/sst2",
            "metrics": {
                "accuracy": 0.85,
                "loss": 0.32,
                "entropy_mean": 0.45
            },
            "timestamp": "27-10-2023"  # Invalid ISO 8601
        }
        with pytest.raises(ValidationError):
            validate(instance=invalid_result, schema=evaluation_result_schema)


class TestSchemaFileIntegrity:
    """Tests to ensure the schema files themselves are valid and loadable."""

    def test_training_schema_exists_and_loadable(self):
        """Verify training config schema file exists and is valid JSON/YAML."""
        assert TRAINING_CONFIG_SCHEMA_PATH.exists(), "training_config.schema.yaml not found"
        try:
            load_schema(TRAINING_CONFIG_SCHEMA_PATH)
        except Exception as e:
            pytest.fail(f"Failed to load training_config.schema.yaml: {e}")

    def test_evaluation_schema_exists_and_loadable(self):
        """Verify evaluation result schema file exists and is valid JSON/YAML."""
        assert EVALUATION_RESULT_SCHEMA_PATH.exists(), "evaluation_result.schema.yaml not found"
        try:
            load_schema(EVALUATION_RESULT_SCHEMA_PATH)
        except Exception as e:
            pytest.fail(f"Failed to load evaluation_result.schema.yaml: {e}")

    def test_schema_compilation(self):
        """Verify schemas can be compiled by Draft7Validator."""
        training_schema = load_schema(TRAINING_CONFIG_SCHEMA_PATH)
        evaluation_schema = load_schema(EVALUATION_RESULT_SCHEMA_PATH)

        try:
            Draft7Validator.check_schema(training_schema)
            Draft7Validator.check_schema(evaluation_schema)
        except Exception as e:
            pytest.fail(f"Schema compilation failed: {e}")
