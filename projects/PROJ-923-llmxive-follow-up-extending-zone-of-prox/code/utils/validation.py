"""
Base validation helpers for llmXive pipeline.
Imports schema contracts and validates data structures against them.
"""
import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml

# Import contract schemas
from contracts.rollout_log import ROLLOUT_LOG_SCHEMA
from contracts.run_metadata import RUN_METADATA_SCHEMA
from contracts.aggregated_metrics import AGGREGATED_METRICS_SCHEMA
from contracts.convergence_result import CONVERGENCE_RESULT_SCHEMA

# Define schema registry for easy access
SCHEMA_REGISTRY = {
    "rollout_log": ROLLOUT_LOG_SCHEMA,
    "run_metadata": RUN_METADATA_SCHEMA,
    "aggregated_metrics": AGGREGATED_METRICS_SCHEMA,
    "convergence_result": CONVERGENCE_RESULT_SCHEMA,
}

def load_schema(schema_name: str) -> Dict[str, Any]:
    """
    Load a schema definition by name from the contracts registry.

    Args:
        schema_name: Key name in SCHEMA_REGISTRY (e.g., 'rollout_log')

    Returns:
        Dictionary containing the schema definition.

    Raises:
        ValueError: If schema_name is not found in registry.
    """
    if schema_name not in SCHEMA_REGISTRY:
        raise ValueError(f"Schema '{schema_name}' not found in registry. "
                         f"Available: {list(SCHEMA_REGISTRY.keys())}")
    return SCHEMA_REGISTRY[schema_name]

def validate_type(value: Any, expected_type: str) -> bool:
    """
    Validate that a value matches the expected Python type.
    Supports simple types and list typing (e.g., 'list[str]').

    Args:
        value: The value to check.
        expected_type: String representation of expected type.

    Returns:
        True if types match, False otherwise.
    """
    if expected_type == "string":
        return isinstance(value, str)
    elif expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    elif expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    elif expected_type == "boolean":
        return isinstance(value, bool)
    elif expected_type == "object":
        return isinstance(value, dict)
    elif expected_type == "array":
        return isinstance(value, list)
    elif expected_type.startswith("list[") and expected_type.endswith("]"):
        inner_type = expected_type[5:-1]
        if not isinstance(value, list):
            return False
        return all(validate_type(item, inner_type) for item in value)
    else:
        # Fallback for unknown types
        return True

def validate_field(value: Any, field_schema: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate a single field against its schema definition.

    Args:
        value: The value to validate.
        field_schema: Dictionary containing field constraints (type, required, etc.).

    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is None.
    """
    field_type = field_schema.get("type")
    required = field_schema.get("required", False)

    # Check required
    if value is None:
        if required:
            return False, f"Required field is missing"
        return True, None

    # Check type
    if field_type and not validate_type(value, field_type):
        return False, f"Expected type '{field_type}', got {type(value).__name__}"

    # Check constraints if present
    if isinstance(value, (int, float)) and "minimum" in field_schema:
        if value < field_schema["minimum"]:
            return False, f"Value {value} is below minimum {field_schema['minimum']}"

    if isinstance(value, str) and "pattern" in field_schema:
        if not re.match(field_schema["pattern"], value):
            return False, f"Value '{value}' does not match pattern '{field_schema['pattern']}'"

    if isinstance(value, dict) and "properties" in field_schema:
        return validate_object(value, field_schema)

    return True, None

def validate_object(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate an object against a schema definition.

    Args:
        data: Dictionary to validate.
        schema: Schema definition with 'properties' and 'required' fields.

    Returns:
        Tuple of (is_valid, error_message).
    """
    properties = schema.get("properties", {})
    required_fields = schema.get("required", [])

    # Check required fields
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: '{field}'"

    # Validate each field
    for key, value in data.items():
        if key in properties:
          valid, error = validate_field(value, properties[key])
          if not valid:
              return False, f"Field '{key}': {error}"
        elif "additionalProperties" in schema and not schema["additionalProperties"]:
            return False, f"Unexpected field: '{key}'"

    return True, None

def validate_against_schema(data: Dict[str, Any], schema_name: str) -> Tuple[bool, List[str]]:
    """
    Validate data against a registered schema.

    Args:
        data: Dictionary to validate.
        schema_name: Name of the schema to use.

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    try:
        schema = load_schema(schema_name)
    except ValueError as e:
        return False, [str(e)]

    if not isinstance(data, dict):
        return False, ["Data must be a dictionary"]

    is_valid, error = validate_object(data, schema)
    if not is_valid:
        return False, [error]

    return True, []

def validate_file(filepath: str, schema_name: str) -> Tuple[bool, List[str]]:
    """
    Validate a JSON/YAML file against a schema.

    Args:
        filepath: Path to the file.
        schema_name: Name of the schema to validate against.

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    if not os.path.exists(filepath):
        return False, [f"File not found: {filepath}"]

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            if filepath.endswith('.yaml') or filepath.endswith('.yml'):
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON: {e}"]
    except yaml.YAMLError as e:
        return False, [f"Invalid YAML: {e}"]
    except Exception as e:
        return False, [f"Failed to read file: {e}"]

    return validate_against_schema(data, schema_name)

def validate_batch(data_list: List[Dict[str, Any]], schema_name: str) -> Dict[str, Any]:
    """
    Validate a list of records against a schema.

    Args:
        data_list: List of dictionaries to validate.
        schema_name: Name of the schema to validate against.

    Returns:
        Dictionary with 'valid_count', 'invalid_count', and 'errors' list.
    """
    valid_count = 0
    invalid_count = 0
    errors = []

    for i, item in enumerate(data_list):
        is_valid, item_errors = validate_against_schema(item, schema_name)
        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1
            for err in item_errors:
                errors.append(f"Record {i}: {err}")

    return {
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "total_count": len(data_list),
        "errors": errors
    }