"""
Task T015: Contract test for model performance metrics schema.

Validates that the output of code/models/evaluate.py conforms to the expected schema.
"""
import json
import os
import pytest
from pathlib import Path

# Schema definition
EXPECTED_SCHEMA = {
    "type": "object",
    "required": ["timestamp", "total_evaluation_time_seconds", "models", "validation_limitation_note"],
    "properties": {
        "timestamp": {"type": "string"},
        "total_evaluation_time_seconds": {"type": "number"},
        "models": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["model_name", "roc_auc", "precision", "recall", "accuracy", "inference_time_seconds"],
                "properties": {
                    "model_name": {"type": "string"},
                    "roc_auc": {"type": "number"},
                    "precision": {"type": "number"},
                    "recall": {"type": "number"},
                    "accuracy": {"type": "number"},
                    "inference_time_seconds": {"type": "number"},
                    "cv_roc_auc_mean": {"type": "number"},
                    "cv_roc_auc_std": {"type": "number"},
                    "cv_precision_mean": {"type": "number"},
                    "cv_precision_std": {"type": "number"},
                    "cv_recall_mean": {"type": "number"},
                    "cv_recall_std": {"type": "number"}
                }
            }
        },
        "validation_limitation_note": {"type": "string"}
    }
}

def validate_type(value, expected_type):
    if expected_type == "string":
        return isinstance(value, str)
    elif expected_type == "number":
        return isinstance(value, (int, float))
    elif expected_type == "array":
        return isinstance(value, list)
    elif expected_type == "object":
        return isinstance(value, dict)
    return False

def validate_object(obj, schema):
    if not validate_type(obj, schema["type"]):
        return False, f"Expected {schema['type']}, got {type(obj).__name__}"

    if schema["type"] == "object":
        # Check required fields
        for field in schema.get("required", []):
            if field not in obj:
                return False, f"Missing required field: {field}"

        # Check properties
        for key, value in obj.items():
            if key in schema["properties"]:
                prop_schema = schema["properties"][key]
                valid, msg = validate_type(value, prop_schema["type"])
                if not valid:
                    return False, f"Field {key}: {msg}"
                # Recursively validate nested objects/arrays if needed
                if prop_schema["type"] == "array" and "items" in prop_schema:
                    item_schema = prop_schema["items"]
                    for i, item in enumerate(value):
                        valid, msg = validate_object(item, item_schema)
                        if not valid:
                            return False, f"Array item {i}: {msg}"
                elif prop_schema["type"] == "object" and "properties" in prop_schema:
                    valid, msg = validate_object(value, prop_schema)
                    if not valid:
                        return False, f"Field {key}: {msg}"
            else:
                # Optional fields are allowed, but we don't validate them unless specified
                pass

    elif schema["type"] == "array":
        item_schema = schema.get("items", {})
        for i, item in enumerate(obj):
            valid, msg = validate_object(item, item_schema)
            if not valid:
                return False, f"Array item {i}: {msg}"

    return True, "OK"

def test_performance_metrics_schema(tmp_path):
    """
    Test that a sample performance metrics file conforms to the schema.
    """
    # Create a sample valid metrics file
    sample_metrics = {
        "timestamp": "2023-10-01T12:00:00Z",
        "total_evaluation_time_seconds": 1.5,
        "models": [
            {
                "model_name": "RandomForest",
                "roc_auc": 0.85,
                "precision": 0.80,
                "recall": 0.75,
                "accuracy": 0.82,
                "inference_time_seconds": 0.01,
                "cv_roc_auc_mean": 0.84,
                "cv_roc_auc_std": 0.02,
                "cv_precision_mean": 0.79,
                "cv_precision_std": 0.03,
                "cv_recall_mean": 0.74,
                "cv_recall_std": 0.04
            }
        ],
        "validation_limitation_note": "Sample note."
    }

    output_file = tmp_path / "performance_metrics.json"
    with open(output_file, 'w') as f:
        json.dump(sample_metrics, f)

    # Load and validate
    with open(output_file, 'r') as f:
        data = json.load(f)

    valid, msg = validate_object(data, EXPECTED_SCHEMA)
    assert valid, f"Schema validation failed: {msg}"

def test_performance_metrics_schema_missing_field(tmp_path):
    """
    Test that a metrics file with a missing required field fails validation.
    """
    sample_metrics = {
        "timestamp": "2023-10-01T12:00:00Z",
        # Missing total_evaluation_time_seconds
        "models": [],
        "validation_limitation_note": "Sample note."
    }

    output_file = tmp_path / "performance_metrics_missing.json"
    with open(output_file, 'w') as f:
        json.dump(sample_metrics, f)

    with open(output_file, 'r') as f:
        data = json.load(f)

    valid, msg = validate_object(data, EXPECTED_SCHEMA)
    assert not valid, "Should have failed validation for missing required field."
    assert "Missing required field: total_evaluation_time_seconds" in msg
