"""
Contract test for metrics.json schema validation.

Task: T020 [US2]
Function: test_metrics_schema_valid
Assert: schema.validate(metrics) using a mock fixture with valid schema-compliant JSON
"""
import os
import json
import pytest
import yaml
from pathlib import Path

# Project root is two levels up from tests/contract/
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
RESULTS_DIR = PROJECT_ROOT / "results"

def load_schema(schema_name: str) -> dict:
    """Load a JSON schema from the contracts directory."""
    schema_path = CONTRACTS_DIR / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r") as f:
        return json.load(f)

def validate_json_against_schema(data: dict, schema: dict) -> bool:
    """
    Validate data against a JSON schema.
    Uses a simple manual validator since jsonschema might not be in requirements.
    Returns True if valid, raises AssertionError if invalid.
    """
    # Basic type checking based on schema
    def check_type(value, expected_type, path="root"):
        type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None)
        }
        if expected_type not in type_map:
            return True  # Unknown type, skip
        
        if not isinstance(value, type_map[expected_type]):
            raise AssertionError(
                f"Type mismatch at {path}: expected {expected_type}, got {type(value).__name__}"
            )

    def validate_object(obj, schema_obj, path="root"):
        if schema_obj.get("type") == "object":
            check_type(obj, "object", path)
            
            properties = schema_obj.get("properties", {})
            required = schema_obj.get("required", [])
            
            # Check required fields
            for req_field in required:
                if req_field not in obj:
                    raise AssertionError(f"Missing required field at {path}: {req_field}")
            
            # Validate properties
            for key, value in obj.items():
                if key in properties:
                    prop_schema = properties[key]
                    if prop_schema.get("type") == "object":
                        validate_object(value, prop_schema, f"{path}.{key}")
                    elif prop_schema.get("type") == "array":
                        check_type(value, "array", f"{path}.{key}")
                        if "items" in prop_schema:
                            item_schema = prop_schema["items"]
                            for i, item in enumerate(value):
                                if item_schema.get("type") == "object":
                                    validate_object(item, item_schema, f"{path}.{key}[{i}]")
                                else:
                                    check_type(item, item_schema.get("type"), f"{path}.{key}[{i}]")
                    else:
                        check_type(value, prop_schema.get("type"), f"{path}.{key}")
        elif schema_obj.get("type") == "array":
            check_type(obj, "array", path)
            if "items" in schema_obj:
                item_schema = schema_obj["items"]
                for i, item in enumerate(obj):
                    if item_schema.get("type") == "object":
                        validate_object(item, item_schema, f"{path}[{i}]")
                    else:
                        check_type(item, item_schema.get("type"), f"{path}[{i}]")
        else:
            check_type(obj, schema_obj.get("type"), path)

    validate_object(data, schema)
    return True

@pytest.fixture
def mock_metrics_data():
    """
    Create a mock fixture with valid schema-compliant JSON data.
    This mimics the structure expected in results/metrics.json.
    """
    return {
        "correlation_coefficients": {
            "flare_flux_dst": {
                "spearman_r": -0.45,
                "p_value": 0.001
            },
            "cme_speed_dst": {
                "spearman_r": -0.62,
                "p_value": 0.0001
            }
        },
        "regression_metrics": {
            "joint_model": {
                "r_squared": 0.38,
                "vif_flare": 2.1,
                "vif_cme": 2.3
            },
            "selected_model_r2": 0.38,
            "selected_model_strategy": "joint"
        },
        "corrected_p_values": {
            "flare_flux_dst": 0.003,
            "cme_speed_dst": 0.0003
        },
        "correction_method": "bonferroni",
        "power_analysis": {
            "effect_size_r": 0.30,
            "sample_size": 150,
            "min_detectable_effect_size": 0.25,
            "power_warning_flag": False
        },
        "non_linear_analysis": {
            "piecewise_r2_improvement": 0.02,
            "improvement_significant": False
        },
        "threshold_analysis": {
            "threshold_candidates": [
                {
                    "cme_speed_kms": 800,
                    "detection_rate": 0.75
                }
            ],
            "threshold_citation_url": "https://www.swpc.noaa.gov/products/geomagnetic-storms"
        },
        "performance": {
            "total_time_seconds": 120.5,
            "peak_ram_mb": 1024.0
        },
        "metadata": {
            "timestamp": "2023-10-27T10:00:00Z",
            "pipeline_version": "1.0.0",
            "data_checksum": "abc123def456"
        }
    }

@pytest.fixture
def metrics_schema():
    """Load the metrics schema from contracts."""
    return load_schema("metrics.schema.yaml")

def test_metrics_schema_valid(mock_metrics_data, metrics_schema):
    """
    Assert: schema.validate(metrics) using a mock fixture with valid schema-compliant JSON.
    
    This test ensures that the metrics data structure produced by the analysis pipeline
    conforms to the defined JSON schema in contracts/metrics.schema.yaml.
    """
    # Validate the mock data against the schema
    # If the schema is invalid or data doesn't match, this will raise an AssertionError
    is_valid = validate_json_against_schema(mock_metrics_data, metrics_schema)
    assert is_valid, "Mock metrics data failed schema validation"

    # Additional check: ensure the schema itself is well-formed
    assert "type" in metrics_schema, "Schema must define a root type"
    assert metrics_schema["type"] == "object", "Root schema type must be object"
    
    # Check that required fields in schema are present in mock data
    required_fields = metrics_schema.get("required", [])
    for field in required_fields:
        assert field in mock_metrics_data, f"Mock data missing required schema field: {field}"
