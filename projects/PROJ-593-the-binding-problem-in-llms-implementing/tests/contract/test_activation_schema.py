"""
Contract test for the ActivationTimeSeries schema.

This test validates that activation time series data produced by the
oscillatory attention mechanism adheres to the expected schema structure.
It ensures that all required fields are present and have the correct data types.
"""

import os
import json
import numpy as np
import pytest
from pathlib import Path
from typing import Any, Dict, List


# Expected schema definition for ActivationTimeSeries
ACTIVATION_SCHEMA = {
    "required_fields": [
        "sequence_id",
        "layer_id",
        "head_id",
        "activation_values",
        "timestamps",
        "frequency_hz",
        "phase_locking_value",
        "spectral_density_correlation",
        "sequence_length",
        "model_name",
        "timestamp_recorded"
    ],
    "field_types": {
        "sequence_id": (str, type(None)),
        "layer_id": int,
        "head_id": int,
        "activation_values": (list, np.ndarray),
        "timestamps": (list, np.ndarray),
        "frequency_hz": (float, int),
        "phase_locking_value": (float, int),
        "spectral_density_correlation": (float, int),
        "sequence_length": int,
        "model_name": str,
        "timestamp_recorded": (str, type(None))
    },
    "array_constraints": {
        "activation_values": {
            "min_length": 1,
            "dtype_check": np.number
        },
        "timestamps": {
            "min_length": 1,
            "dtype_check": np.number
        }
    }
}


def _validate_field_types(record: Dict[str, Any]) -> List[str]:
    """Validate that all fields have correct types."""
    errors = []
    for field, expected_types in ACTIVATION_SCHEMA["field_types"].items():
        if field not in record:
            errors.append(f"Missing required field: {field}")
            continue

        value = record[field]
        if not isinstance(expected_types, tuple):
            expected_types = (expected_types,)

        # Handle numpy arrays specially
        if isinstance(value, np.ndarray):
            if not any(isinstance(value, t) for t in expected_types):
                errors.append(f"Field {field} has wrong type: {type(value)}, expected {expected_types}")
        elif not any(isinstance(value, t) for t in expected_types):
            errors.append(f"Field {field} has wrong type: {type(value)}, expected {expected_types}")

    return errors


def _validate_array_constraints(record: Dict[str, Any]) -> List[str]:
    """Validate array-specific constraints."""
    errors = []
    for field, constraints in ACTIVATION_SCHEMA["array_constraints"].items():
        if field not in record:
            continue

        value = record[field]
        if isinstance(value, (list, np.ndarray)):
            if len(value) < constraints["min_length"]:
                errors.append(f"Field {field} has length {len(value)}, minimum required: {constraints['min_length']}")

            if constraints.get("dtype_check"):
                for i, item in enumerate(value):
                    if not isinstance(item, constraints["dtype_check"]):
                        errors.append(f"Field {field}[{i}] has wrong dtype: {type(item)}")
                        break
        else:
            errors.append(f"Field {field} is not an array: {type(value)}")

    return errors


def test_activation_schema_structure():
    """Test that a valid ActivationTimeSeries record matches the schema."""
    # Create a valid sample record
    valid_record = {
        "sequence_id": "test_seq_001",
        "layer_id": 1,
        "head_id": 2,
        "activation_values": np.random.randn(100).tolist(),
        "timestamps": np.linspace(0, 1, 100).tolist(),
        "frequency_hz": 40.0,
        "phase_locking_value": 0.75,
        "spectral_density_correlation": 0.68,
        "sequence_length": 100,
        "model_name": "distilbert-base-uncased",
        "timestamp_recorded": "2024-01-01T00:00:00Z"
    }

    # Validate field types
    type_errors = _validate_field_types(valid_record)
    assert len(type_errors) == 0, f"Type validation failed: {type_errors}"

    # Validate array constraints
    array_errors = _validate_array_constraints(valid_record)
    assert len(array_errors) == 0, f"Array validation failed: {array_errors}"

    # Check all required fields are present
    for field in ACTIVATION_SCHEMA["required_fields"]:
        assert field in valid_record, f"Required field missing: {field}"


def test_activation_schema_missing_fields():
    """Test that missing required fields are detected."""
    incomplete_record = {
        "sequence_id": "test_seq_001",
        "layer_id": 1,
        # Missing head_id and other fields
        "activation_values": [1, 2, 3],
        "timestamps": [0, 1, 2]
    }

    type_errors = _validate_field_types(incomplete_record)
    assert len(type_errors) > 0, "Should detect missing required fields"
    assert any("Missing required field" in error for error in type_errors)


def test_activation_schema_wrong_types():
    """Test that wrong field types are detected."""
    invalid_record = {
        "sequence_id": "test_seq_001",
        "layer_id": "not_an_int",  # Wrong type
        "head_id": 2,
        "activation_values": "not_an_array",  # Wrong type
        "timestamps": [0, 1, 2],
        "frequency_hz": 40.0,
        "phase_locking_value": 0.75,
        "spectral_density_correlation": 0.68,
        "sequence_length": 3,
        "model_name": "distilbert-base-uncased",
        "timestamp_recorded": "2024-01-01T00:00:00Z"
    }

    type_errors = _validate_field_types(invalid_record)
    assert len(type_errors) > 0, "Should detect wrong field types"


def test_activation_schema_empty_arrays():
    """Test that empty arrays are rejected."""
    invalid_record = {
        "sequence_id": "test_seq_001",
        "layer_id": 1,
        "head_id": 2,
        "activation_values": [],  # Empty array
        "timestamps": [],  # Empty array
        "frequency_hz": 40.0,
        "phase_locking_value": 0.75,
        "spectral_density_correlation": 0.68,
        "sequence_length": 0,
        "model_name": "distilbert-base-uncased",
        "timestamp_recorded": "2024-01-01T00:00:00Z"
    }

    array_errors = _validate_array_constraints(invalid_record)
    assert len(array_errors) > 0, "Should detect empty arrays"


def test_activation_schema_json_serializable(tmp_path: Path):
    """Test that valid records can be serialized to JSON."""
    valid_record = {
        "sequence_id": "test_seq_001",
        "layer_id": 1,
        "head_id": 2,
        "activation_values": np.random.randn(10).tolist(),
        "timestamps": np.linspace(0, 1, 10).tolist(),
        "frequency_hz": 40.0,
        "phase_locking_value": 0.75,
        "spectral_density_correlation": 0.68,
        "sequence_length": 10,
        "model_name": "distilbert-base-uncased",
        "timestamp_recorded": "2024-01-01T00:00:00Z"
    }

    # Convert to JSON string
    json_str = json.dumps(valid_record)
    assert len(json_str) > 0

    # Parse back
    parsed = json.loads(json_str)
    assert parsed["sequence_id"] == valid_record["sequence_id"]
    assert parsed["layer_id"] == valid_record["layer_id"]
    assert len(parsed["activation_values"]) == len(valid_record["activation_values"])


def test_activation_schema_numpy_arrays():
    """Test that numpy arrays are handled correctly."""
    valid_record = {
        "sequence_id": "test_seq_001",
        "layer_id": 1,
        "head_id": 2,
        "activation_values": np.random.randn(100),
        "timestamps": np.linspace(0, 1, 100),
        "frequency_hz": 40.0,
        "phase_locking_value": 0.75,
        "spectral_density_correlation": 0.68,
        "sequence_length": 100,
        "model_name": "distilbert-base-uncased",
        "timestamp_recorded": "2024-01-01T00:00:00Z"
    }

    type_errors = _validate_field_types(valid_record)
    assert len(type_errors) == 0, f"Numpy arrays should be valid: {type_errors}"

    array_errors = _validate_array_constraints(valid_record)
    assert len(array_errors) == 0, f"Numpy arrays should pass constraints: {array_errors}"