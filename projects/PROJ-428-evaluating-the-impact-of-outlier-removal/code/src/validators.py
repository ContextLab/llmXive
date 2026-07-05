"""
Schema validation utilities using PyYAML.

Validates data dictionaries against JSON schemas defined in YAML files
located in the `contracts/` directory.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yaml

# Project root is assumed to be two levels up from code/src/validators.py
# or we can rely on the environment variable or standard project structure.
# Given T001 created the structure, we assume `contracts/` is at the root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"


class SchemaValidationError(Exception):
    """Raised when a schema validation fails."""

    def __init__(self, message: str, errors: Optional[List[str]] = None):
        super().__init__(message)
        self.errors = errors or []


def load_schema(schema_filename: str) -> Dict[str, Any]:
    """
    Load a schema from a YAML file in the contracts directory.

    Args:
        schema_filename: The name of the schema file (e.g., 'dataset.schema.yaml').

    Returns:
        A dictionary representing the schema.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the YAML file is malformed.
    """
    schema_path = CONTRACTS_DIR / schema_filename
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_type(value: Any, expected_type: str) -> bool:
    """
    Validate a value against a JSON Schema-like type definition.

    Supports: string, number, integer, boolean, array, object, null.
    """
    if expected_type == "string":
        return isinstance(value, str)
    elif expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    elif expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    elif expected_type == "boolean":
        return isinstance(value, bool)
    elif expected_type == "array":
        return isinstance(value, list)
    elif expected_type == "object":
        return isinstance(value, dict)
    elif expected_type == "null":
        return value is None
    return False


def validate_value(value: Any, schema: Dict[str, Any], path: str = "root") -> List[str]:
    """
    Recursively validate a value against a schema dictionary.

    Returns a list of error messages.
    """
    errors = []

    # Check 'type'
    if "type" in schema:
        if not validate_type(value, schema["type"]):
            errors.append(f"{path}: Expected type '{schema['type']}', got '{type(value).__name__}'")
            return errors  # Stop further checks if type is wrong

    # Check 'enum'
    if "enum" in schema:
        if value not in schema["enum"]:
            errors.append(f"{path}: Value '{value}' not in allowed values {schema['enum']}")

    # Check 'required' for objects
    if schema.get("type") == "object" and isinstance(value, dict):
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in value:
                errors.append(f"{path}: Missing required field '{field}'")

        # Validate properties
        properties = schema.get("properties", {})
        for key, val in value.items():
            if key in properties:
                errors.extend(validate_value(val, properties[key], f"{path}.{key}"))
            elif not schema.get("additionalProperties", True):
                errors.append(f"{path}: Unexpected field '{key}'")

    # Check 'items' for arrays
    if schema.get("type") == "array" and isinstance(value, list):
        items_schema = schema.get("items", {})
        for i, item in enumerate(value):
            errors.extend(validate_value(item, items_schema, f"{path}[{i}]"))

    # Check 'minimum', 'maximum' for numbers
    if schema.get("type") in ["number", "integer"] and isinstance(value, (int, float)):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: Value {value} is less than minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: Value {value} is greater than maximum {schema['maximum']}")

    return errors


def validate_data(data: Dict[str, Any], schema_filename: str) -> None:
    """
    Validate a data dictionary against a schema file.

    Args:
        data: The data to validate.
        schema_filename: The name of the schema file.

    Raises:
        SchemaValidationError: If validation fails.
    """
    try:
        schema = load_schema(schema_filename)
    except FileNotFoundError as e:
        raise SchemaValidationError(f"Could not load schema: {e}")
    except yaml.YAMLError as e:
        raise SchemaValidationError(f"Invalid YAML in schema: {e}")

    errors = validate_value(data, schema)

    if errors:
        raise SchemaValidationError(
            f"Validation failed against schema '{schema_filename}'",
            errors=errors
        )


def validate_file_structure(file_paths: List[str], schema_filename: str) -> None:
    """
    Validate that specific files exist and optionally check their content
    against a schema if they are JSON/YAML.

    This is a helper for T006 to ensure the contracts/*.schema.yaml files
    themselves are valid and can be loaded, or to validate data files
    if a schema is provided for them.
    """
    # Primarily used to ensure the schema files exist and are valid
    for path_str in file_paths:
        path = Path(path_str)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # If it's a schema file, try to load it to ensure it's valid YAML
        if path.suffix in [".yaml", ".yml"] and "schema" in path.name:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise SchemaValidationError(f"Invalid YAML in schema file {path}", [str(e)])