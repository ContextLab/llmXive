"""
Schema validation utilities for the chatbot politeness research pipeline.

This module provides functionality to validate datasets against defined
JSON schemas, ensuring data integrity before processing.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml


class SchemaValidationError(Exception):
    """Raised when dataset validation against a schema fails."""
    pass


def load_schema(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a JSON schema from a YAML or JSON file.

    Args:
        schema_path: Path to the schema file.

    Returns:
        The loaded schema as a dictionary.
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")

    with open(path, 'r', encoding='utf-8') as f:
        if path.suffix in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        elif path.suffix == '.json':
            return json.load(f)
        else:
            raise ValueError(f"Unsupported schema format: {path.suffix}")


def validate_type(value: Any, expected_type: str, field_path: str) -> List[str]:
    """
    Validate that a value matches the expected JSON Schema type.

    Args:
        value: The value to validate.
        expected_type: The expected type (e.g., 'string', 'integer', 'number', 'boolean', 'array', 'object', 'null').
        field_path: The path to the field for error reporting.

    Returns:
        A list of error messages (empty if valid).
    """
    errors = []

    type_mapping = {
        'string': str,
        'integer': int,
        'number': (int, float),
        'boolean': bool,
        'array': list,
        'object': dict,
        'null': type(None)
    }

    if expected_type not in type_mapping:
        # Handle 'anyOf' or complex types later if needed
        return errors

    expected_python_type = type_mapping[expected_type]

    # Special case: in JSON, booleans are distinct from integers, but Python treats them as ints
    if expected_type == 'integer' and isinstance(value, bool):
        errors.append(f"Field '{field_path}': Expected 'integer', got 'boolean'")
        return errors
    if expected_type == 'number' and isinstance(value, bool):
        errors.append(f"Field '{field_path}': Expected 'number', got 'boolean'")
        return errors

    if not isinstance(value, expected_python_type):
        actual_type = type(value).__name__
        errors.append(f"Field '{field_path}': Expected '{expected_type}', got '{actual_type}'")

    return errors


def validate_value_constraints(value: Any, constraints: Dict[str, Any], field_path: str) -> List[str]:
    """
    Validate value constraints (min, max, minLength, etc.).

    Args:
        value: The value to validate.
        constraints: The constraint definitions from the schema.
        field_path: The path to the field for error reporting.

    Returns:
        A list of error messages.
    """
    errors = []

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if 'minimum' in constraints and value < constraints['minimum']:
            errors.append(f"Field '{field_path}': Value {value} is less than minimum {constraints['minimum']}")
        if 'maximum' in constraints and value > constraints['maximum']:
            errors.append(f"Field '{field_path}': Value {value} is greater than maximum {constraints['maximum']}")
        if 'exclusiveMinimum' in constraints and value <= constraints['exclusiveMinimum']:
            errors.append(f"Field '{field_path}': Value {value} is not greater than {constraints['exclusiveMinimum']}")
        if 'exclusiveMaximum' in constraints and value >= constraints['exclusiveMaximum']:
            errors.append(f"Field '{field_path}': Value {value} is not less than {constraints['exclusiveMaximum']}")

    if isinstance(value, str):
        if 'minLength' in constraints and len(value) < constraints['minLength']:
            errors.append(f"Field '{field_path}': String length {len(value)} is less than minLength {constraints['minLength']}")
        if 'maxLength' in constraints and len(value) > constraints['maxLength']:
            errors.append(f"Field '{field_path}': String length {len(value)} is greater than maxLength {constraints['maxLength']}")
        if 'pattern' in constraints:
            if not re.match(constraints['pattern'], value):
                errors.append(f"Field '{field_path}': Value '{value}' does not match pattern '{constraints['pattern']}'")
        if 'enum' in constraints and value not in constraints['enum']:
            errors.append(f"Field '{field_path}': Value '{value}' is not in allowed values {constraints['enum']}")

    if isinstance(value, list):
        if 'minItems' in constraints and len(value) < constraints['minItems']:
            errors.append(f"Field '{field_path}': Array length {len(value)} is less than minItems {constraints['minItems']}")
        if 'maxItems' in constraints and len(value) > constraints['maxItems']:
            errors.append(f"Field '{field_path}': Array length {len(value)} is greater than maxItems {constraints['maxItems']}")

    return errors


def validate_object(data: Dict[str, Any], schema: Dict[str, Any], path: str = "") -> List[str]:
    """
    Validate an object against a JSON schema definition.

    Args:
        data: The data to validate.
        schema: The schema definition.
        path: The current path in the data structure.

    Returns:
        A list of error messages.
    """
    errors = []

    # Check required fields
    if 'required' in schema:
        for field in schema['required']:
            if field not in data:
                field_path = f"{path}.{field}" if path else field
                errors.append(f"Missing required field: '{field_path}'")

    # Validate properties
    properties = schema.get('properties', {})
    for key, value in data.items():
        field_path = f"{path}.{key}" if path else key

        if key in properties:
            prop_schema = properties[key]

            # Type validation
            if 'type' in prop_schema:
                type_errors = validate_type(value, prop_schema['type'], field_path)
                errors.extend(type_errors)

            # Constraint validation
            if value is not None and not isinstance(value, bool):
                constraint_errors = validate_value_constraints(value, prop_schema, field_path)
                errors.extend(constraint_errors)

            # Nested object validation
            if prop_schema.get('type') == 'object' and isinstance(value, dict):
                nested_errors = validate_object(value, prop_schema, field_path)
                errors.extend(nested_errors)

            # Array item validation
            if prop_schema.get('type') == 'array' and isinstance(value, list):
                items_schema = prop_schema.get('items', {})
                for idx, item in enumerate(value):
                    item_path = f"{field_path}[{idx}]"
                    if items_schema.get('type') == 'object' and isinstance(item, dict):
                        nested_errors = validate_object(item, items_schema, item_path)
                        errors.extend(nested_errors)
                    elif 'type' in items_schema:
                        type_errors = validate_type(item, items_schema['type'], item_path)
                        errors.extend(type_errors)
        else:
            # Additional properties check (if not allowed)
            if not schema.get('additionalProperties', True):
                errors.append(f"Additional property not allowed: '{field_path}'")

    return errors


def validate_dataset(data: Union[Dict[str, Any], List[Dict[str, Any]], Path], schema_path: Union[str, Path]) -> Tuple[bool, List[str]]:
    """
    Validate a dataset against a schema.

    Args:
        data: The data to validate (dict, list of dicts, or path to JSON/Parquet).
        schema_path: Path to the schema file.

    Returns:
        A tuple of (is_valid, errors).
    """
    schema = load_schema(schema_path)

    # Handle file paths
    if isinstance(data, Path):
        if not data.exists():
            return False, [f"Data file not found: {data}"]

        if data.suffix == '.json':
            with open(data, 'r', encoding='utf-8') as f:
                data = json.load(f)
        elif data.suffix == '.parquet':
            try:
                import pandas as pd
                df = pd.read_parquet(data)
                # Convert to list of dicts for validation
                data = df.to_dict('records')
            except ImportError:
                return False, ["pandas is required to read parquet files"]
            except Exception as e:
                return False, [f"Error reading parquet file: {str(e)}"]
        else:
            return False, [f"Unsupported data format: {data.suffix}"]

    # Validate single object
    if isinstance(data, dict):
        errors = validate_object(data, schema)
        return len(errors) == 0, errors

    # Validate list of objects
    if isinstance(data, list):
        all_errors = []
        for idx, item in enumerate(data):
            if not isinstance(item, dict):
                all_errors.append(f"Item {idx} is not an object")
                continue
            item_errors = validate_object(item, schema)
            if item_errors:
                for err in item_errors:
                    all_errors.append(f"Item {idx}: {err}")
        return len(all_errors) == 0, all_errors

    return False, ["Data must be a dictionary or list of dictionaries"]


def validate_dataset_schema(data_path: Union[str, Path], schema_path: Union[str, Path] = "contracts/dataset.schema.yaml") -> bool:
    """
    Validate a dataset file against its schema.

    Args:
        data_path: Path to the dataset file (JSON or Parquet).
        schema_path: Path to the schema file.

    Returns:
        True if validation passes, raises SchemaValidationError otherwise.
    """
    is_valid, errors = validate_dataset(data_path, schema_path)

    if not is_valid:
        error_msg = "Schema validation failed:\n" + "\n".join(f"  - {err}" for err in errors)
        raise SchemaValidationError(error_msg)

    return True


def get_missing_fields(data_path: Union[str, Path], schema_path: Union[str, Path] = "contracts/dataset.schema.yaml") -> List[str]:
    """
    Get a list of missing required fields in the dataset.

    Args:
        data_path: Path to the dataset file.
        schema_path: Path to the schema file.

    Returns:
        A list of missing field names.
    """
    schema = load_schema(schema_path)
    required_fields = schema.get('required', [])
    missing = []

    if isinstance(data_path, Path):
        if data_path.suffix == '.parquet':
            try:
                import pandas as pd
                df = pd.read_parquet(data_path)
                existing_fields = set(df.columns)
            except Exception:
                return required_fields
        elif data_path.suffix == '.json':
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    existing_fields = set(data[0].keys())
                else:
                    existing_fields = set(data.keys()) if isinstance(data, dict) else set()
        else:
            return required_fields
    else:
        return required_fields

    for field in required_fields:
        if field not in existing_fields:
            missing.append(field)

    return missing