"""
Contract Test for Model Output Schema (T018)

Validates that model outputs produced by the training/evaluation pipeline
conform to the schema defined in specs/model_schema.yaml.

This test ensures:
1. All required fields are present.
2. Data types match the schema (e.g., predictions are floats, not strings).
3. Metric values are within reasonable bounds (e.g., R2 <= 1.0).
4. Arrays (predictions, targets) have matching lengths.
"""

import os
import sys
import json
import pytest
import numpy as np
from pathlib import Path
from typing import Dict, Any
import yaml

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

SCHEMA_PATH = PROJECT_ROOT / "specs" / "model_schema.yaml"
TEST_OUTPUT_PATH = PROJECT_ROOT / "results" / "reports" / "model_comparison.json"

def load_schema() -> Dict[str, Any]:
    """Load the model output schema from YAML."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)

def validate_type(value: Any, expected_type: str, field_path: str) -> None:
    """Validate that a value matches the expected type."""
    type_map = {
        "string": str,
        "number": (int, float),
        "integer": int,
        "boolean": bool,
        "array": list,
        "object": dict,
    }

    expected = type_map.get(expected_type)
    if expected is None:
        raise ValueError(f"Unknown type in schema: {expected_type}")

    if not isinstance(value, expected):
        raise TypeError(
            f"Field '{field_path}' has type {type(value).__name__}, "
            f"expected {expected_type}"
        )

def validate_object(obj: Dict[str, Any], schema: Dict[str, Any], path: str = "") -> None:
    """Recursively validate an object against a schema."""
    # Check required fields
    required = schema.get("required", [])
    for field in required:
        if field not in obj:
            raise AssertionError(f"Missing required field: {path}.{field}")

    # Validate properties
    properties = schema.get("properties", {})
    for key, value in obj.items():
        if key not in properties:
            # Allow extra properties if not strictly forbidden, but warn
            # For strict contract testing, we might want to raise:
            # raise ValueError(f"Unexpected field: {path}.{key}")
            continue

        prop_schema = properties[key]
        current_path = f"{path}.{key}" if path else key

        # Validate type
        if "type" in prop_schema:
            validate_type(value, prop_schema["type"], current_path)

        # Validate array items
        if prop_schema["type"] == "array" and "items" in prop_schema:
            item_schema = prop_schema["items"]
            for i, item in enumerate(value):
                validate_type(item, item_schema["type"], f"{current_path}[{i}]")

        # Validate nested objects
        if prop_schema["type"] == "object" and "properties" in prop_schema:
            validate_object(value, prop_schema, current_path)

        # Validate enum
        if "enum" in prop_schema:
            if value not in prop_schema["enum"]:
                raise AssertionError(
                    f"Field '{current_path}' value '{value}' not in allowed values: {prop_schema['enum']}"
                )

        # Validate minimum (for numbers/ints)
        if "minimum" in prop_schema:
            if value < prop_schema["minimum"]:
                raise AssertionError(
                    f"Field '{current_path}' value {value} is less than minimum {prop_schema['minimum']}"
                )

        # Validate pattern (for strings)
        if "pattern" in prop_schema and isinstance(value, str):
            import re
            if not re.match(prop_schema["pattern"], value):
                raise AssertionError(
                    f"Field '{current_path}' value '{value}' does not match pattern '{prop_schema['pattern']}'"
                )

@pytest.fixture(scope="module")
def schema() -> Dict[str, Any]:
    """Load the schema once for the test module."""
    return load_schema()

@pytest.fixture(scope="module")
def test_output() -> Dict[str, Any]:
    """
    Load the test output file.
    If the file doesn't exist, this test is skipped or marked as pending
    depending on the CI configuration.
    """
    if not TEST_OUTPUT_PATH.exists():
        pytest.skip(f"Test output file not found: {TEST_OUTPUT_PATH}. "
                    "Run the training pipeline first to generate this file.")

    with open(TEST_OUTPUT_PATH, "r") as f:
        return json.load(f)

def test_model_output_schema_conformance(schema: Dict[str, Any], test_output: Dict[str, Any]):
    """
    Main contract test: Validates the structure and types of the model output.
    """
    try:
        validate_object(test_output, schema)
    except (TypeError, AssertionError, ValueError) as e:
        pytest.fail(f"Schema validation failed: {e}")

def test_predictions_and_targets_length_match(test_output: Dict[str, Any]):
    """
    Contract test: Ensures predictions and targets arrays have the same length.
    """
    preds = test_output.get("predictions", [])
    targets = test_output.get("targets", [])

    assert len(preds) == len(targets), (
        f"Mismatch in array lengths: predictions ({len(preds)}) != targets ({len(targets)})"
    )

def test_metrics_reasonable_bounds(test_output: Dict[str, Any]):
    """
    Contract test: Validates that calculated metrics are physically/numerically reasonable.
    - R2 should be <= 1.0 (can be negative for bad models, but usually > -inf)
    - MAE and RMSE should be >= 0
    """
    metrics = test_output.get("metrics", {})

    mae = metrics.get("mae", -1)
    rmse = metrics.get("rmse", -1)
    r2 = metrics.get("r2", 2.0)

    assert mae >= 0, f"MAE must be non-negative, got {mae}"
    assert rmse >= 0, f"RMSE must be non-negative, got {rmse}"
    assert r2 <= 1.0, f"R2 cannot be greater than 1.0, got {r2}"

def test_model_name_format(test_output: Dict[str, Any]):
    """
    Contract test: Validates model_name follows the allowed pattern.
    """
    import re
    model_name = test_output.get("model_name", "")
    pattern = r"^[A-Za-z0-9_]+$"
    assert re.match(pattern, model_name), (
        f"Model name '{model_name}' does not match pattern {pattern}"
    )

def test_metadata_timestamp_format(test_output: Dict[str, Any]):
    """
    Contract test: Validates timestamp is in ISO 8601 format.
    """
    from datetime import datetime
    metadata = test_output.get("metadata", {})
    timestamp_str = metadata.get("timestamp", "")

    try:
        # Attempt to parse ISO 8601
        datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    except ValueError:
        pytest.fail(f"Timestamp '{timestamp_str}' is not a valid ISO 8601 format")