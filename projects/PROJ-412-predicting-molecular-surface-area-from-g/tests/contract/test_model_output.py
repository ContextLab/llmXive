"""
Contract test for model output schema (T019).
Validates model output artifacts against data/schemas/model_schema.yaml.
"""
import json
import os
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

SCHEMA_PATH = PROJECT_ROOT / "data" / "schemas" / "model_schema.yaml"


def load_schema() -> Dict[str, Any]:
    """Load the model output schema from YAML."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)


def validate_type(value: Any, expected_type: str, field_path: str) -> List[str]:
    """Validate a value against an expected type string."""
    errors = []

    type_mapping = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "object": dict,
    }

    if expected_type not in type_mapping:
        errors.append(f"Unknown type '{expected_type}' at {field_path}")
        return errors

    expected_python_type = type_mapping[expected_type]

    # Special handling for number (int or float)
    if expected_type == "number":
        if not isinstance(value, (int, float)):
            errors.append(f"Field '{field_path}' expected number, got {type(value).__name__}")
    elif not isinstance(value, expected_python_type):
        errors.append(f"Field '{field_path}' expected {expected_type}, got {type(value).__name__}")

    return errors


def validate_enum(value: Any, allowed_values: List[str], field_path: str) -> List[str]:
    """Validate a value against an enum list."""
    if value not in allowed_values:
        return [f"Field '{field_path}' value '{value}' not in allowed values: {allowed_values}"]
    return []


def validate_object(
    data: Dict[str, Any],
    schema: Dict[str, Any],
    parent_path: str = ""
) -> List[str]:
    """Recursively validate an object against a schema."""
    errors = []

    # Check required fields
    required_fields = schema.get("required", [])
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {parent_path}.{field}")

    # Check properties
    properties = schema.get("properties", {})
    for field_name, field_schema in properties.items():
        field_path = f"{parent_path}.{field_name}" if parent_path else field_name

        if field_name not in data:
            continue  # Optional field, skip if not present

        value = data[field_name]
        field_type = field_schema.get("type")

        # Type validation
        if field_type:
            errors.extend(validate_type(value, field_type, field_path))

        # Enum validation
        if "enum" in field_schema:
            errors.extend(validate_enum(value, field_schema["enum"], field_path))

        # Nested object validation
        if field_type == "object" and isinstance(value, dict):
            nested_schema = field_schema
            # Handle nested required fields
            if "required" in field_schema:
                for req_field in field_schema["required"]:
                    if req_field not in value:
                        errors.append(f"Missing required field in nested object: {field_path}.{req_field}")
            # Recursively validate nested properties
            if "properties" in field_schema:
                errors.extend(validate_object(value, field_schema, field_path))

        # Nested object with additionalProperties
        if field_type == "object" and field_schema.get("additionalProperties") is True:
            # For hyperparameters, we allow any key-value pairs
            if not isinstance(value, dict):
                errors.append(f"Field '{field_path}' expected object, got {type(value).__name__}")

    # Check additionalProperties constraint
    if schema.get("additionalProperties") is False:
        allowed_keys = set(properties.keys())
        for key in data.keys():
            if key not in allowed_keys:
                errors.append(f"Unexpected field '{parent_path}.{key}' in object")

    return errors


class TestModelOutputSchema(unittest.TestCase):
    """Contract tests for model output schema validation."""

    @classmethod
    def setUpClass(cls):
        """Load the schema once for all tests."""
        try:
            cls.schema = load_schema()
        except FileNotFoundError as e:
            cls.skipTest(str(e))

    def test_schema_exists_and_is_valid(self):
        """Test that the schema file exists and is valid YAML."""
        self.assertIsNotNone(self.schema)
        self.assertIn("type", self.schema)
        self.assertEqual(self.schema["type"], "object")
        self.assertIn("required", self.schema)
        self.assertIn("properties", self.schema)

    def test_required_fields_present(self):
        """Test that all required fields are defined in the schema."""
        required_fields = self.schema.get("required", [])
        expected_fields = ["model_type", "metrics", "hyperparameters", "timestamp", "dataset_checksum"]
        for field in expected_fields:
            self.assertIn(field, required_fields, f"Required field '{field}' missing from schema")

    def test_model_type_enum_values(self):
        """Test that model_type has valid enum values."""
        model_type_schema = self.schema["properties"]["model_type"]
        self.assertIn("enum", model_type_schema)
        valid_types = model_type_schema["enum"]
        expected_types = ["GCN", "GeometryOracle", "Baseline2D", "BaselineGeometry", "RandomForest", "Baseline3D"]
        for expected in expected_types:
            self.assertIn(expected, valid_types, f"Expected model type '{expected}' not in schema")

    def test_metrics_structure(self):
        """Test that metrics object has correct structure."""
        metrics_schema = self.schema["properties"]["metrics"]
        self.assertIn("required", metrics_schema)
        self.assertIn("properties", metrics_schema)

        required_metrics = metrics_schema["required"]
        for metric in ["mae", "rmse", "r2"]:
            self.assertIn(metric, required_metrics, f"Metric '{metric}' required in metrics object")

        metric_properties = metrics_schema["properties"]
        for metric in ["mae", "rmse", "r2"]:
            self.assertIn(metric, metric_properties)
            self.assertEqual(metric_properties[metric]["type"], "number")

    def test_hyperparameters_structure(self):
        """Test that hyperparameters object allows additional properties."""
        hyper_schema = self.schema["properties"]["hyperparameters"]
        self.assertTrue(hyper_schema.get("additionalProperties", False))
        self.assertEqual(hyper_schema["type"], "object")

    def test_validate_valid_model_output(self):
        """Test validation of a valid model output artifact."""
        valid_output = {
            "model_type": "GCN",
            "metrics": {
                "mae": 0.05,
                "rmse": 0.08,
                "r2": 0.95,
                "comparison": {
                    "p_value": 0.03,
                    "cohen_d": 0.5
                }
            },
            "hyperparameters": {
                "learning_rate": 0.001,
                "batch_size": 32,
                "epochs": 50
            },
            "timestamp": "2024-01-15T10:30:00Z",
            "dataset_checksum": "abc123def456"
        }

        errors = validate_object(valid_output, self.schema)
        self.assertEqual(len(errors), 0, f"Valid output should have no errors: {errors}")

    def test_validate_invalid_model_type(self):
        """Test validation fails for invalid model_type."""
        invalid_output = {
            "model_type": "InvalidModel",
            "metrics": {
                "mae": 0.05,
                "rmse": 0.08,
                "r2": 0.95
            },
            "hyperparameters": {},
            "timestamp": "2024-01-15T10:30:00Z",
            "dataset_checksum": "abc123def456"
        }

        errors = validate_object(invalid_output, self.schema)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("model_type" in e for e in errors))

    def test_validate_missing_required_field(self):
        """Test validation fails for missing required field."""
        invalid_output = {
            "model_type": "GCN",
            "metrics": {
                "mae": 0.05,
                "rmse": 0.08,
                "r2": 0.95
            },
            # Missing hyperparameters, timestamp, dataset_checksum
            "timestamp": "2024-01-15T10:30:00Z"
        }

        errors = validate_object(invalid_output, self.schema)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("hyperparameters" in e or "dataset_checksum" in e for e in errors))

    def test_validate_invalid_metric_type(self):
        """Test validation fails for non-numeric metric."""
        invalid_output = {
            "model_type": "GCN",
            "metrics": {
                "mae": "not_a_number",
                "rmse": 0.08,
                "r2": 0.95
            },
            "hyperparameters": {},
            "timestamp": "2024-01-15T10:30:00Z",
            "dataset_checksum": "abc123def456"
        }

        errors = validate_object(invalid_output, self.schema)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("mae" in e for e in errors))

    def test_validate_unexpected_field(self):
        """Test validation fails for unexpected fields."""
        invalid_output = {
            "model_type": "GCN",
            "metrics": {
                "mae": 0.05,
                "rmse": 0.08,
                "r2": 0.95
            },
            "hyperparameters": {},
            "timestamp": "2024-01-15T10:30:00Z",
            "dataset_checksum": "abc123def456",
            "unexpected_field": "should_not_be_here"
        }

        errors = validate_object(invalid_output, self.schema)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("unexpected_field" in e for e in errors))

    def test_validate_all_model_types(self):
        """Test validation passes for all allowed model types."""
        valid_types = ["GCN", "GeometryOracle", "Baseline2D", "BaselineGeometry", "RandomForest", "Baseline3D"]

        for model_type in valid_types:
          valid_output = {
              "model_type": model_type,
              "metrics": {
                  "mae": 0.05,
                  "rmse": 0.08,
                  "r2": 0.95
              },
              "hyperparameters": {},
              "timestamp": "2024-01-15T10:30:00Z",
              "dataset_checksum": "abc123def456"
          }
          errors = validate_object(valid_output, self.schema)
          self.assertEqual(len(errors), 0, f"Valid model type '{model_type}' should pass validation: {errors}")


if __name__ == "__main__":
    unittest.main()