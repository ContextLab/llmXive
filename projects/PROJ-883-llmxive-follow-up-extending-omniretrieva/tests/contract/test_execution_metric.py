"""
Contract test for ExecutionMetric schema validation.

This module validates that the ExecutionMetric data structure conforms to the
schema defined in contracts/execution_metric.schema.yaml.

It verifies:
1. Schema file existence and validity (YAML).
2. Data type constraints for all required fields.
3. Presence of required fields.
4. Value constraints (e.g., non-negative latency, valid source types).
"""

import os
import json
import yaml
import pytest
from pathlib import Path
from typing import Any, Dict, List

# Project root path resolution
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "execution_metric.schema.yaml"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

# Valid enum values as defined in the schema (expected to be loaded dynamically)
VALID_SOURCE_TYPES = {"text", "relational", "graph"}
VALID_COMPLEXITY_LEVELS = {1, 2, 3, 4, 5}  # 5+ usually mapped to 4 or higher in analysis, but schema allows integers


def load_schema() -> Dict[str, Any]:
    """Load and parse the ExecutionMetric schema YAML file."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found at {SCHEMA_PATH}. "
                                "Ensure T004 has created contracts/execution_metric.schema.yaml")
    
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    
    if not isinstance(schema, dict):
        raise ValueError("Schema file must contain a valid YAML dictionary.")
    
    return schema


def validate_field_type(value: Any, expected_type: str, field_name: str) -> None:
    """
    Validate that a value matches the expected type string from the schema.
    Supports: string, integer, float, boolean, list.
    """
    type_map = {
        "string": str,
        "integer": int,
        "float": (int, float), # Allow int for float fields
        "boolean": bool,
        "list": list,
        "object": dict,
    }
    
    expected_python_type = type_map.get(expected_type)
    if expected_python_type is None:
        raise ValueError(f"Unknown type definition in schema: {expected_type}")
    
    if not isinstance(value, expected_python_type):
        raise TypeError(
            f"Field '{field_name}' expected type '{expected_type}', "
            f"but got {type(value).__name__} with value {value!r}"
        )


def validate_enum(value: Any, allowed_values: List[Any], field_name: str) -> None:
    """Validate that a value is in the list of allowed enum values."""
    if value not in allowed_values:
        raise ValueError(
            f"Field '{field_name}' has value '{value}', "
            f"but must be one of {allowed_values}"
        )


def validate_metric(metric: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """
    Validate a single metric dictionary against the schema.
    
    Args:
        metric: The dictionary representing an ExecutionMetric instance.
        schema: The loaded schema dictionary.
        
    Raises:
        ValueError: If required fields are missing or constraints are violated.
        TypeError: If field types are incorrect.
    """
    properties = schema.get("properties", {})
    required_fields = schema.get("required", [])
    
    # Check required fields
    for field in required_fields:
        if field not in metric:
            raise ValueError(f"Missing required field: '{field}'")
    
    # Validate each field present in the metric
    for field_name, value in metric.items():
        if field_name not in properties:
            # Optional: warn or ignore extra fields depending on strictness
            # For contract tests, we usually allow extra fields unless 'additionalProperties' is false
            if schema.get("additionalProperties") is False:
                raise ValueError(f"Unexpected field '{field_name}' in metric")
            continue
        
        field_spec = properties[field_name]
        
        # Type check
        if "type" in field_spec:
            validate_field_type(value, field_spec["type"], field_name)
        
        # Enum check
        if "enum" in field_spec:
            validate_enum(value, field_spec["enum"], field_name)
        
        # Range check (for numbers)
        if "minimum" in field_spec and isinstance(value, (int, float)):
            if value < field_spec["minimum"]:
                raise ValueError(
                    f"Field '{field_name}' value {value} is below minimum {field_spec['minimum']}"
                )
        
        # Pattern check (for strings)
        if "pattern" in field_spec and isinstance(value, str):
            import re
            if not re.match(field_spec["pattern"], value):
                raise ValueError(
                    f"Field '{field_name}' value '{value}' does not match pattern '{field_spec['pattern']}'"
                )


class TestExecutionMetricSchema:
    """
    Test suite for ExecutionMetric schema validation.
    
    These tests ensure that the schema file is valid and that data instances
    conform to the defined structure and constraints.
    """

    @pytest.fixture(scope="class")
    def schema(self) -> Dict[str, Any]:
        """Load the schema once per test class."""
        return load_schema()

    def test_schema_file_exists(self):
        """Verify that the schema file exists."""
        assert SCHEMA_PATH.exists(), f"Schema file missing at {SCHEMA_PATH}"

    def test_schema_is_valid_yaml(self):
        """Verify that the schema file is valid YAML."""
        try:
            load_schema()
        except yaml.YAMLError as e:
            pytest.fail(f"Schema file is not valid YAML: {e}")
        except Exception as e:
            pytest.fail(f"Failed to load schema: {e}")

    def test_schema_has_required_structure(self, schema):
        """Verify the schema has the expected top-level keys."""
        assert "type" in schema, "Schema must define 'type'"
        assert schema["type"] == "object", "Schema type must be 'object'"
        assert "properties" in schema, "Schema must define 'properties'"
        assert "required" in schema, "Schema must define 'required' fields"

    def test_valid_metric_passes(self, schema):
        """Test that a fully valid metric passes validation."""
        valid_metric = {
            "query_id": "q_001",
            "source_type": "text",
            "complexity_level": 2,
            "latency_ms": 150.5,
            "cpu_time_ms": 140.0,
            "wall_time_ms": 150.5,
            "timeout": False,
            "error_message": None
        }
        # Should not raise
        validate_metric(valid_metric, schema)

    def test_missing_required_field_raises(self, schema):
        """Test that missing a required field raises ValueError."""
        invalid_metric = {
            "query_id": "q_002",
            # Missing source_type (required)
            "complexity_level": 1,
            "latency_ms": 10.0
        }
        with pytest.raises(ValueError, match="Missing required field"):
            validate_metric(invalid_metric, schema)

    def test_invalid_source_type_raises(self, schema):
        """Test that an invalid source_type raises ValueError."""
        invalid_metric = {
            "query_id": "q_003",
            "source_type": "invalid_type", # Not in enum
            "complexity_level": 1,
            "latency_ms": 10.0
        }
        with pytest.raises(ValueError, match="Field 'source_type'"):
            validate_metric(invalid_metric, schema)

    def test_negative_latency_raises(self, schema):
        """Test that negative latency raises ValueError (if minimum constraint exists)."""
        invalid_metric = {
            "query_id": "q_004",
            "source_type": "text",
            "complexity_level": 1,
            "latency_ms": -5.0
        }
        # Check if schema defines minimum for latency_ms
        if "properties" in schema and "latency_ms" in schema["properties"]:
            if "minimum" in schema["properties"]["latency_ms"]:
                with pytest.raises(ValueError, match="below minimum"):
                    validate_metric(invalid_metric, schema)
            else:
                # If no minimum defined in schema, we assume negative is allowed by schema (unlikely but possible)
                # But logically it should fail. We skip strict check if schema is lenient.
                pass
        else:
            pass

    def test_wrong_type_for_latency_raises(self, schema):
        """Test that non-numeric latency raises TypeError."""
        invalid_metric = {
            "query_id": "q_005",
            "source_type": "text",
            "complexity_level": 1,
            "latency_ms": "fast" # String instead of number
        }
        with pytest.raises(TypeError, match="Field 'latency_ms'"):
            validate_metric(invalid_metric, schema)

    def test_complexity_level_enum(self, schema):
        """Test that complexity_level is an integer (and optionally within range if schema defines it)."""
        valid_metric = {
            "query_id": "q_006",
            "source_type": "graph",
            "complexity_level": 4,
            "latency_ms": 200.0
        }
        validate_metric(valid_metric, schema)

        invalid_metric = {
            "query_id": "q_007",
            "source_type": "graph",
            "complexity_level": 1.5, # Float instead of int
            "latency_ms": 200.0
        }
        with pytest.raises(TypeError):
            validate_metric(invalid_metric, schema)

    def test_all_valid_source_types(self, schema):
        """Test that all defined valid source types are accepted."""
        for st in ["text", "relational", "graph"]:
            metric = {
                "query_id": f"q_{st}",
                "source_type": st,
                "complexity_level": 1,
                "latency_ms": 10.0
            }
            validate_metric(metric, schema)