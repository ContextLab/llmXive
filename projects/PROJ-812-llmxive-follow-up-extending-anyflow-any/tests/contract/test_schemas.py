import json
import os
from pathlib import Path

import pytest
from jsonschema import validate, ValidationError, Draft7Validator

# Define the path to the contracts directory
CONTRACTS_DIR = Path(__file__).parent.parent.parent / "contracts"

SCHEMA_FILES = {
    "annotation": "annotation_schema.json",
    "metric": "metric_schema.json",
    "result": "result_schema.json",
    "sensitivity": "sensitivity_schema.json"
}

@pytest.fixture
def schemas():
    """Load all schemas from the contracts directory."""
    loaded_schemas = {}
    for key, filename in SCHEMA_FILES.items():
        filepath = CONTRACTS_DIR / filename
        assert filepath.exists(), f"Schema file not found: {filepath}"
        with open(filepath, 'r', encoding='utf-8') as f:
            loaded_schemas[key] = json.load(f)
    return loaded_schemas

def test_schemas_are_valid_json(schemas):
    """Ensure all schema files are valid JSON."""
    for key, schema in schemas.items():
        assert isinstance(schema, dict), f"Schema {key} is not a valid JSON object"
        assert "$schema" in schema, f"Schema {key} missing $schema definition"

def test_schemas_conform_to_draft7(schemas):
    """Ensure all schemas conform to JSON Schema Draft 7."""
    for key, schema in schemas.items():
        try:
            Draft7Validator.check_schema(schema)
        except ValidationError as e:
            pytest.fail(f"Schema {key} is invalid: {e.message}")

def test_annotation_schema_has_required_fields(schemas):
    """Verify annotation schema has required fields."""
    required = ["video_id", "file_path", "score", "annotator_id", "timestamp"]
    for field in required:
        assert field in schemas["annotation"]["required"], f"Missing required field: {field}"

def test_metric_schema_has_required_fields(schemas):
    """Verify metric schema has required fields."""
    required = ["clip_id", "divergence", "kurtosis", "temporal_clustering", "n_steps", "baseline_type"]
    for field in required:
        assert field in schemas["metric"]["required"], f"Missing required field: {field}"

def test_result_schema_has_required_fields(schemas):
    """Verify result schema has required fields."""
    required = ["analysis_id", "pearson_r", "spearman_rho", "p_value", "sample_size", "method"]
    for field in required:
        assert field in schemas["result"]["required"], f"Missing required field: {field}"

def test_sensitivity_schema_has_required_fields(schemas):
    """Verify sensitivity schema has required fields."""
    required = ["threshold", "n_steps", "true_positives", "true_negatives", "false_positives", "false_negatives", "precision", "recall", "f1_score"]
    for field in required:
        assert field in schemas["sensitivity"]["required"], f"Missing required field: {field}"

def test_sample_annotation_validates(schemas):
    """Test a sample annotation against the schema."""
    sample = {
        "video_id": "vid_001",
        "file_path": "data/raw/clips/vid_001.mp4",
        "score": 0.85,
        "annotator_id": "expert_01",
        "timestamp": "2023-10-27T10:00:00Z",
        "is_adjudicated": False
    }
    validate(instance=sample, schema=schemas["annotation"])

def test_sample_metric_validates(schemas):
    """Test a sample metric against the schema."""
    sample = {
        "clip_id": "vid_001",
        "divergence": 0.12,
        "kurtosis": 2.5,
        "temporal_clustering": 0.9,
        "n_steps": 500,
        "baseline_type": "euler"
    }
    validate(instance=sample, schema=schemas["metric"])

def test_sample_result_validates(schemas):
    """Test a sample result against the schema."""
    sample = {
        "analysis_id": "run_001",
        "pearson_r": 0.75,
        "spearman_rho": 0.78,
        "p_value": 0.001,
        "sample_size": 500,
        "method": "pearson",
        "ipw_applied": True
    }
    validate(instance=sample, schema=schemas["result"])

def test_sample_sensitivity_validates(schemas):
    """Test a sample sensitivity entry against the schema."""
    sample = {
        "threshold": 0.5,
        "n_steps": 500,
        "true_positives": 45,
        "true_negatives": 40,
        "false_positives": 5,
        "false_negatives": 10,
        "precision": 0.90,
        "recall": 0.82,
        "f1_score": 0.86
    }
    validate(instance=sample, schema=schemas["sensitivity"])
