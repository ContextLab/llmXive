"""
Contract test for model output schema (T018).

Validates that model output artifacts (JSON) conform to the schema defined
in data/schemas/model_schema.yaml.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

import pytest
import yaml

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "data" / "schemas" / "model_schema.yaml"
RESULTS_DIR = PROJECT_ROOT / "results" / "reports"

def load_schema() -> Dict[str, Any]:
    """Load the model output schema from YAML."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found: {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)

def validate_required_fields(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """Check that all required fields are present."""
    required = schema.get("required", [])
    missing = [field for field in required if field not in data]
    return missing

def validate_type(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """Validate field types against schema definitions."""
    errors = []
    properties = schema.get("properties", {})
    
    for field, expected_schema in properties.items():
        if field not in data:
            continue
        
        value = data[field]
        expected_type = expected_schema.get("type")
        
        if expected_type == "string":
            if not isinstance(value, str):
                errors.append(f"Field '{field}' expected string, got {type(value).__name__}")
        elif expected_type == "number":
            if not isinstance(value, (int, float)):
                errors.append(f"Field '{field}' expected number, got {type(value).__name__}")
        elif expected_type == "integer":
            if not isinstance(value, int):
                errors.append(f"Field '{field}' expected integer, got {type(value).__name__}")
        elif expected_type == "object":
            if not isinstance(value, dict):
                errors.append(f"Field '{field}' expected object, got {type(value).__name__}")
        elif expected_type == "array":
            if not isinstance(value, list):
                errors.append(f"Field '{field}' expected array, got {type(value).__name__}")
        
        # Validate nested objects recursively
        if expected_type == "object" and isinstance(value, dict):
            nested_errors = validate_type(value, expected_schema)
            errors.extend([f"{field}.{err}" for err in nested_errors])

    return errors

def validate_enum(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """Validate enum constraints."""
    errors = []
    properties = schema.get("properties", {})
    
    for field, expected_schema in properties.items():
        if field not in data:
            continue
        
        value = data[field]
        enum_values = expected_schema.get("enum")
        
        if enum_values and value not in enum_values:
            errors.append(f"Field '{field}' value '{value}' not in allowed enum: {enum_values}")
        
        # Check nested enums
        if expected_schema.get("type") == "object" and isinstance(value, dict):
            nested_errors = validate_enum(value, expected_schema)
            errors.extend([f"{field}.{err}" for err in nested_errors])

def validate_additional_properties(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """Ensure no additional properties are present if forbidden."""
    errors = []
    properties = schema.get("properties", {})
    additional_allowed = schema.get("additionalProperties", True)
    
    if not additional_allowed:
        allowed_keys = set(properties.keys())
        actual_keys = set(data.keys())
        extra = actual_keys - allowed_keys
        if extra:
            errors.append(f"Additional properties not allowed: {extra}")
    
    return errors

def validate_timestamp_format(data: Dict[str, Any]) -> List[str]:
    """Validate ISO 8601 timestamp format."""
    errors = []
    if "timestamp" in data:
        try:
            # Try parsing ISO format
            datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        except ValueError:
            errors.append("Field 'timestamp' is not a valid ISO 8601 format")
    return errors

def validate_metrics_structure(data: Dict[str, Any]) -> List[str]:
    """Specific validation for the metrics nested object."""
    errors = []
    if "metrics" not in data:
        return errors
    
    metrics = data["metrics"]
    required_metrics = ["mae", "rmse", "r2"]
    
    for metric in required_metrics:
        if metric not in metrics:
            errors.append(f"Missing required metric: {metric}")
        elif not isinstance(metrics[metric], (int, float)):
            errors.append(f"Metric '{metric}' must be a number")
        elif metrics[metric] < 0 and metric != "r2":
            # MAE and RMSE should be non-negative
            errors.append(f"Metric '{metric}' should be non-negative")
    
    return errors

@pytest.fixture(scope="module")
def schema():
    return load_schema()

@pytest.mark.contract
def test_schema_exists():
    """Verify the schema file exists."""
    assert SCHEMA_PATH.exists(), f"Schema file missing at {SCHEMA_PATH}"

@pytest.mark.contract
def test_schema_valid_yaml(schema):
    """Verify the schema is valid YAML and has required root keys."""
    assert isinstance(schema, dict)
    assert "type" in schema
    assert schema["type"] == "object"

@pytest.mark.contract
def test_sample_output_conforms(schema):
    """Test a manually constructed valid sample against the schema."""
    sample = {
        "model_type": "GCN",
        "metrics": {
            "mae": 0.5,
            "rmse": 0.7,
            "r2": 0.85
        },
        "hyperparameters": {
            "hidden_channels": 64,
            "num_layers": 3
        },
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "dataset_checksum": "abc123def456",
        "split_info": {
            "train_size": 100,
            "test_size": 20
        }
    }
    
    # Run all validators
    missing = validate_required_fields(sample, schema)
    assert not missing, f"Missing required fields: {missing}"
    
    type_errors = validate_type(sample, schema)
    assert not type_errors, f"Type errors: {type_errors}"
    
    enum_errors = validate_enum(sample, schema)
    assert not enum_errors, f"Enum errors: {enum_errors}"
    
    add_errors = validate_additional_properties(sample, schema)
    assert not add_errors, f"Additional property errors: {add_errors}"
    
    ts_errors = validate_timestamp_format(sample)
    assert not ts_errors, f"Timestamp errors: {ts_errors}"
    
    metric_errors = validate_metrics_structure(sample)
    assert not metric_errors, f"Metric structure errors: {metric_errors}"

@pytest.mark.contract
def test_actual_report_files(schema):
    """
    If model comparison reports exist in results/reports, validate them.
    This test is skipped if no reports are found (e.g., pipeline not run yet).
    """
    if not RESULTS_DIR.exists():
        pytest.skip("Results directory not found")
    
    report_files = list(RESULTS_DIR.glob("*.json"))
    if not report_files:
        pytest.skip("No JSON report files found in results/reports")
    
    for report_path in report_files:
        with open(report_path, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                pytest.fail(f"Invalid JSON in {report_path}")
        
        # Validate against schema
        missing = validate_required_fields(data, schema)
        if missing:
            pytest.fail(f"File {report_path.name} missing required fields: {missing}")
        
        type_errors = validate_type(data, schema)
        if type_errors:
            pytest.fail(f"File {report_path.name} type errors: {type_errors}")
        
        metric_errors = validate_metrics_structure(data)
        if metric_errors:
            pytest.fail(f"File {report_path.name} metric errors: {metric_errors}")