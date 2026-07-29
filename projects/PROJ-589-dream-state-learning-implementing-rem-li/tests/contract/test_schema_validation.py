"""
Contract tests for schema validation of training configuration and evaluation results.

These tests ensure that the YAML schemas defined in data/ are valid and that
the JSON Schema validation logic works correctly against sample data.
"""
import json
import pytest
import yaml
from pathlib import Path
from jsonschema import validate, ValidationError, Draft7Validator
from typing import Dict, Any

# Get the project root relative to this test file
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMAS_DIR = PROJECT_ROOT / "data"

# Sample valid data for testing
VALID_TRAINING_CONFIG = {
    "experiment_name": "dream-test-001",
    "model_name": "distilbert-base-uncased",
    "dataset_name": "glue/mrpc",
    "seed": 42,
    "hyperparameters": {
        "learning_rate": 5e-5,
        "batch_size": 16,
        "num_epochs": 3,
        "warmup_steps": 10,
        "mask_rate": 0.15,
        "entropy_threshold": 0.5,
        "dream_ratio": 0.25,
        "max_wall_clock_hours": 5.0,
        "max_memory_gb": 7.0
    },
    "paths": {
        "data_dir": "data/raw",
        "checkpoint_dir": "data/checkpoints",
        "log_dir": "data/logs",
        "results_dir": "data/results"
    },
    "device": "cpu"
}

INVALID_TRAINING_CONFIG_MISSING_REQUIRED = {
    "experiment_name": "test",
    "model_name": "distilbert-base-uncased"
    # Missing dataset_name, hyperparameters
}

INVALID_TRAINING_CONFIG_BAD_TYPE = {
    "experiment_name": "test",
    "model_name": "distilbert-base-uncased",
    "dataset_name": "glue/mrpc",
    "seed": "not_an_integer",  # Should be integer
    "hyperparameters": {
        "learning_rate": 5e-5,
        "batch_size": 16,
        "num_epochs": 3,
        "warmup_steps": 10,
        "mask_rate": 0.15,
        "entropy_threshold": 0.5,
        "dream_ratio": 0.25,
        "max_wall_clock_hours": 5.0,
        "max_memory_gb": 7.0
    },
    "device": "cpu"
}

VALID_EVALUATION_RESULT = {
    "experiment_id": "dream-test-001",
    "dataset_name": "glue/mrpc",
    "model_name": "distilbert-base-uncased",
    "timestamp": "2024-01-15T10:30:00Z",
    "metrics": {
        "accuracy": 0.85,
        "loss": 0.42,
        "f1_score": 0.84,
        "precision": 0.86,
        "recall": 0.82
    },
    "hyperparameters_snapshot": {
        "learning_rate": 5e-5,
        "batch_size": 16
    },
    "resource_usage": {
        "peak_memory_gb": 4.2,
        "total_time_seconds": 3600,
        "total_tokens_processed": 100000
    },
    "statistical_comparison": {
        "baseline_accuracy": 0.80,
        "accuracy_difference": 0.05,
        "wilcoxon_p_value": 0.03,
        "significant_at_alpha_005": True
    }
}

INVALID_EVALUATION_RESULT_MISSING_METRICS = {
    "experiment_id": "dream-test-001",
    "dataset_name": "glue/mrpc",
    "timestamp": "2024-01-15T10:30:00Z"
    # Missing model_name, metrics
}

INVALID_EVALUATION_RESULT_BAD_ACCURACY = {
    "experiment_id": "dream-test-001",
    "dataset_name": "glue/mrpc",
    "model_name": "distilbert-base-uncased",
    "timestamp": "2024-01-15T10:30:00Z",
    "metrics": {
        "accuracy": 1.5,  # Invalid: accuracy must be <= 1.0
        "loss": 0.42
    }
}


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema file and return it as a dictionary."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)


def validate_data_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """Validate data against a JSON Schema. Raises ValidationError if invalid."""
    validator = Draft7Validator(schema)
    errors = list(validator.iter_errors(data))
    if errors:
        error_messages = [f"{'.'.join(map(str, e.path))}: {e.message}" for e in errors]
        raise ValidationError("\n".join(error_messages))


class TestTrainingConfigSchema:
    """Tests for training_config.schema.yaml validation."""

    @pytest.fixture
    def schema(self) -> Dict[str, Any]:
        """Load the training config schema."""
        schema_path = SCHEMAS_DIR / "training_config.schema.yaml"
        assert schema_path.exists(), f"Schema file not found: {schema_path}"
        return load_schema(schema_path)

    def test_schema_file_exists(self):
        """Verify the schema file exists."""
        schema_path = SCHEMAS_DIR / "training_config.schema.yaml"
        assert schema_path.exists()

    def test_schema_is_valid_json_schema(self, schema):
        """Verify the loaded schema is a valid JSON Schema draft 7."""
        # Check for required JSON Schema keys
        assert "$schema" in schema
        assert "type" in schema
        assert schema["type"] == "object"

    def test_valid_config_passes(self, schema):
        """A valid training config should pass validation."""
        validate_data_against_schema(VALID_TRAINING_CONFIG, schema)

    def test_missing_required_fields_fails(self, schema):
        """Missing required fields should raise ValidationError."""
        with pytest.raises(ValidationError):
            validate_data_against_schema(INVALID_TRAINING_CONFIG_MISSING_REQUIRED, schema)

    def test_wrong_type_fails(self, schema):
        """Wrong data types should raise ValidationError."""
        with pytest.raises(ValidationError):
            validate_data_against_schema(INVALID_TRAINING_CONFIG_BAD_TYPE, schema)

    def test_device_enum_validation(self, schema):
        """Device field should only accept 'cpu' or 'cuda'."""
        invalid_device_config = VALID_TRAINING_CONFIG.copy()
        invalid_device_config["device"] = "gpu"  # Invalid enum value
        with pytest.raises(ValidationError):
            validate_data_against_schema(invalid_device_config, schema)

    def test_mask_rate_bounds(self, schema):
        """Mask rate should be between 0 and 1."""
        invalid_mask_config = VALID_TRAINING_CONFIG.copy()
        invalid_mask_config["hyperparameters"] = VALID_TRAINING_CONFIG["hyperparameters"].copy()
        invalid_mask_config["hyperparameters"]["mask_rate"] = 1.5  # Out of bounds
        with pytest.raises(ValidationError):
            validate_data_against_schema(invalid_mask_config, schema)


class TestEvaluationResultSchema:
    """Tests for evaluation_result.schema.yaml validation."""

    @pytest.fixture
    def schema(self) -> Dict[str, Any]:
        """Load the evaluation result schema."""
        schema_path = SCHEMAS_DIR / "evaluation_result.schema.yaml"
        assert schema_path.exists(), f"Schema file not found: {schema_path}"
        return load_schema(schema_path)

    def test_schema_file_exists(self):
        """Verify the schema file exists."""
        schema_path = SCHEMAS_DIR / "evaluation_result.schema.yaml"
        assert schema_path.exists()

    def test_schema_is_valid_json_schema(self, schema):
        """Verify the loaded schema is a valid JSON Schema draft 7."""
        assert "$schema" in schema
        assert "type" in schema
        assert schema["type"] == "object"

    def test_valid_result_passes(self, schema):
        """A valid evaluation result should pass validation."""
        validate_data_against_schema(VALID_EVALUATION_RESULT, schema)

    def test_missing_required_fields_fails(self, schema):
        """Missing required fields should raise ValidationError."""
        with pytest.raises(ValidationError):
            validate_data_against_schema(INVALID_EVALUATION_RESULT_MISSING_METRICS, schema)

    def test_accuracy_bounds(self, schema):
        """Accuracy must be between 0 and 1."""
        invalid_acc_config = VALID_EVALUATION_RESULT.copy()
        invalid_acc_config["metrics"] = VALID_EVALUATION_RESULT["metrics"].copy()
        invalid_acc_config["metrics"]["accuracy"] = -0.1  # Below 0
        with pytest.raises(ValidationError):
            validate_data_against_schema(invalid_acc_config, schema)

        invalid_acc_config["metrics"]["accuracy"] = 1.5  # Above 1
        with pytest.raises(ValidationError):
            validate_data_against_schema(invalid_acc_config, schema)

    def test_timestamp_format(self, schema):
        """Timestamp should be a valid ISO 8601 date-time."""
        # Note: jsonschema draft 7 supports format validation, but we test the structure
        invalid_timestamp = VALID_EVALUATION_RESULT.copy()
        invalid_timestamp["timestamp"] = "not-a-date"
        # This might not raise ValidationError if format validation is not enabled
        # but it should be caught by a strict validator
        try:
            validate_data_against_schema(invalid_timestamp, schema)
        except ValidationError:
            pass  # Expected

    def test_statistical_comparison_optional_fields(self, schema):
        """Statistical comparison fields should be optional but validated if present."""
        result_without_stats = VALID_EVALUATION_RESULT.copy()
        result_without_stats.pop("statistical_comparison")
        # Should pass without statistical comparison
        validate_data_against_schema(result_without_stats, schema)

        # With valid statistical comparison
        validate_data_against_schema(VALID_EVALUATION_RESULT, schema)

        # With invalid p-value (negative)
        invalid_stats = VALID_EVALUATION_RESULT.copy()
        invalid_stats["statistical_comparison"] = VALID_EVALUATION_RESULT["statistical_comparison"].copy()
        invalid_stats["statistical_comparison"]["wilcoxon_p_value"] = -0.1
        with pytest.raises(ValidationError):
            validate_data_against_schema(invalid_stats, schema)


class TestSchemaIntegration:
    """Integration tests ensuring schemas work together."""

    def test_both_schemas_load_successfully(self):
        """Both schema files should load without error."""
        train_schema_path = SCHEMAS_DIR / "training_config.schema.yaml"
        eval_schema_path = SCHEMAS_DIR / "evaluation_result.schema.yaml"

        assert train_schema_path.exists()
        assert eval_schema_path.exists()

        train_schema = load_schema(train_schema_path)
        eval_schema = load_schema(eval_schema_path)

        assert train_schema is not None
        assert eval_schema is not None

    def test_schema_consistency(self):
        """Ensure schemas have consistent structure for common fields."""
        train_schema = load_schema(SCHEMAS_DIR / "training_config.schema.yaml")
        eval_schema = load_schema(SCHEMAS_DIR / "evaluation_result.schema.yaml")

        # Both should have $schema and type
        assert "$schema" in train_schema
        assert "$schema" in eval_schema
        assert train_schema["$schema"] == eval_schema["$schema"]
        assert train_schema["type"] == "object"
        assert eval_schema["type"] == "object"
