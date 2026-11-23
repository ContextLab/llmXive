"""
Contract tests for classifier output schema.
Validates the structure of the logistic regression prediction report.
"""
import pytest
from typing import Any, Dict

CLASSIFIER_SCHEMA = {
    "type": "object",
    "required": ["accuracy", "precision", "recall", "auc_roc", "sample_size"],
    "properties": {
        "accuracy": {"type": "number"},
        "precision": {"type": "number"},
        "recall": {"type": "number"},
        "auc_roc": {"type": "number"},
        "sample_size": {"type": "integer"},
        "model_type": {"type": "string"}
    }
}

def validate_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """Basic schema validator for classifier output."""
    if not isinstance(data, dict):
        raise ValueError(f"Expected dict, got {type(data)}")

    for field in schema.get("required", []):
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    for field, rules in schema.get("properties", {}).items():
        if field in data:
            val = data[field]
            if rules["type"] == "number" and not isinstance(val, (int, float)):
                raise ValueError(f"Field {field} must be number")
            elif rules["type"] == "integer" and not isinstance(val, int):
                raise ValueError(f"Field {field} must be integer")
            elif rules["type"] == "string" and not isinstance(val, str):
                raise ValueError(f"Field {field} must be string")

def test_validate_valid_classifier_report():
    """Test that a valid report passes validation"""
    valid_report = {
        "accuracy": 0.75,
        "precision": 0.70,
        "recall": 0.68,
        "auc_roc": 0.78,
        "sample_size": 100,
        "model_type": "LogisticRegression"
    }
    validate_schema(valid_report, CLASSIFIER_SCHEMA)

def test_validate_missing_auc_roc():
    """Test that missing auc_roc raises error"""
    invalid_report = {
        "accuracy": 0.75,
        "precision": 0.70,
        "recall": 0.68,
        "sample_size": 100
    }
    with pytest.raises(ValueError):
        validate_schema(invalid_report, CLASSIFIER_SCHEMA)

def test_validate_wrong_type_accuracy():
    """Test that string accuracy raises error"""
    invalid_report = {
        "accuracy": "0.75",  # Should be number
        "precision": 0.70,
        "recall": 0.68,
        "auc_roc": 0.78,
        "sample_size": 100
    }
    with pytest.raises(ValueError):
        validate_schema(invalid_report, CLASSIFIER_SCHEMA)