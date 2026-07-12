"""
Contract test for model artifact schema.
Validates that model outputs conform to the expected structure.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import get_path, ensure_dir


class TestModelSchema:
    """
    Contract tests for model artifact schema validation.
    """

    def test_schema_validation_function_exists(self):
        """Verify that the schema validation utility exists and is importable."""
        from tests.contract.schema_validator import validate_json_schema
        assert callable(validate_json_schema)

    def test_model_schema_definition(self):
        """Verify the model schema definition exists."""
        from tests.contract.schema_validator import MODEL_SCHEMA
        assert isinstance(MODEL_SCHEMA, dict)
        assert "type" in MODEL_SCHEMA
        assert MODEL_SCHEMA["type"] == "object"

    def test_validate_valid_model_artifact(self):
        """Test validation against a valid model artifact."""
        from tests.contract.schema_validator import validate_json_schema, MODEL_SCHEMA

        valid_artifact = {
            "model_type": "LogisticRegression",
            "model_path": "models/jailbreak_classifier.joblib",
            "training_config": {
                "n_samples": 1000,
                "n_features": 384,
                "train_split_ratio": 0.8
            },
            "metrics": {
                "accuracy": 0.85,
                "precision": 0.82,
                "recall": 0.88,
                "f1_score": 0.85
            },
            "timestamp": "2024-01-01T12:00:00Z"
        }

        is_valid, errors = validate_json_schema(valid_artifact, MODEL_SCHEMA)
        assert is_valid, f"Valid artifact failed validation: {errors}"

    def test_validate_missing_required_field(self):
        """Test validation fails when required field is missing."""
        from tests.contract.schema_validator import validate_json_schema, MODEL_SCHEMA

        invalid_artifact = {
            "model_type": "LogisticRegression",
            "training_config": {},
            "metrics": {}
            # Missing 'model_path' and 'timestamp'
        }

        is_valid, errors = validate_json_schema(invalid_artifact, MODEL_SCHEMA)
        assert not is_valid
        assert len(errors) > 0

    def test_validate_wrong_metric_type(self):
        """Test validation fails when metric has wrong type."""
        from tests.contract.schema_validator import validate_json_schema, MODEL_SCHEMA

        invalid_artifact = {
            "model_type": "LogisticRegression",
            "model_path": "models/test.joblib",
            "training_config": {
                "n_samples": "not_an_int",  # Should be integer
                "n_features": 384,
                "train_split_ratio": 0.8
            },
            "metrics": {
                "accuracy": 0.85
            },
            "timestamp": "2024-01-01T12:00:00Z"
        }

        is_valid, errors = validate_json_schema(invalid_artifact, MODEL_SCHEMA)
        assert not is_valid

    def test_validate_invalid_label(self):
        """Test validation fails for invalid label in anomaly score."""
        from tests.contract.schema_validator import validate_json_schema, ANOMALY_SCORE_SCHEMA

        invalid_record = {
            "file_id": "test_001",
            "mahalanobis_distance": 5.2,
            "label": "unknown",  # Not in enum
            "is_anomaly": True
        }

        is_valid, errors = validate_json_schema(invalid_record, ANOMALY_SCORE_SCHEMA)
        assert not is_valid
