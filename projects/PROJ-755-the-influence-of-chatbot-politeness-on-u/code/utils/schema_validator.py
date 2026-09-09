"""
Schema Validator for Dialogue Datasets.

This module provides functions to validate datasets against the defined
JSON Schema in `contracts/dataset.schema.yaml`. It ensures data integrity
and compliance with the project's data model before processing.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
import yaml


class SchemaValidationError(Exception):
    """Custom exception for schema validation errors."""
    pass


def load_schema(schema_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Load the JSON schema from the specified path.

    Args:
        schema_path: Path to the schema YAML file. Defaults to
                     'contracts/dataset.schema.yaml'.

    Returns:
        Dictionary containing the schema definition.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the schema file is not valid YAML/JSON.
    """
    if schema_path is None:
        schema_path = Path("contracts/dataset.schema.yaml")
    else:
        schema_path = Path(schema_path)

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)

    return schema


def validate_type(value: Any, expected_type: str) -> bool:
    """
    Validate if a value matches the expected JSON Schema type.

    Args:
        value: The value to check.
        expected_type: The expected type string (e.g., 'string', 'integer', 'array').

    Returns:
        True if the type matches, False otherwise.
    """
    if value is None:
        return True  # Null handling is separate in constraints

    type_map = {
        'string': str,
        'integer': int,
        'number': (int, float),
        'boolean': bool,
        'array': list,
        'object': dict,
    }

    expected_python_type = type_map.get(expected_type)
    if expected_python_type is None:
        return False

    return isinstance(value, expected_python_type)


def validate_value_constraints(value: Any, constraints: Dict[str, Any]) -> bool:
    """
    Validate value constraints like minimum, maximum, minLength, enum.

    Args:
        value: The value to check.
        constraints: Dictionary of constraints from the schema.

    Returns:
        True if constraints are met, False otherwise.
    """
    if value is None:
        return True

    if 'minimum' in constraints and value < constraints['minimum']:
        return False
    if 'maximum' in constraints and value > constraints['maximum']:
        return False
    if 'minLength' in constraints and isinstance(value, str) and len(value) < constraints['minLength']:
        return False
    if 'maxLength' in constraints and isinstance(value, str) and len(value) > constraints['maxLength']:
        return False
    if 'enum' in constraints and value not in constraints['enum']:
        return False

    return True


def validate_property(value: Any, prop_schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a single property against its schema definition.

    Args:
        value: The value to validate.
        prop_schema: The schema definition for this property.

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []

    # Type check
    if 'type' in prop_schema:
        if not validate_type(value, prop_schema['type']):
            errors.append(f"Type mismatch: expected {prop_schema['type']}, got {type(value).__name__}")
            return False, errors

    # Constraints check
    if not validate_value_constraints(value, prop_schema):
        errors.append(f"Constraint violation: {value} does not meet {prop_schema}")
        return False, errors

    # Nested object check (for 'properties' inside an object type)
    if prop_schema.get('type') == 'object' and 'properties' in prop_schema:
        if not isinstance(value, dict):
            return False, ["Expected object for nested properties"]
        # Recursively validate nested properties if needed, but for dataset
        # validation we usually check columns, so this is structural.
        # For now, we assume the structure is handled by the dataframe column check.

    # Array items check
    if prop_schema.get('type') == 'array' and 'items' in prop_schema:
        if not isinstance(value, list):
            return False, ["Expected list for array type"]
        item_schema = prop_schema['items']
        for idx, item in enumerate(value):
            valid, item_errors = validate_property(item, item_schema)
            if not valid:
                errors.append(f"Item {idx} invalid: {item_errors}")
                return False, errors

    return True, errors


def validate_object(obj: Dict[str, Any], schema_def: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate an object (dictionary) against a schema definition.

    Args:
        obj: The object to validate.
        schema_def: The schema definition for this object type.

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []

    # Check required fields
    required_fields = schema_def.get('required', [])
    for field in required_fields:
        if field not in obj:
            errors.append(f"Missing required field: {field}")

    # Check properties
    properties = schema_def.get('properties', {})
    for key, value in obj.items():
        if key in properties:
            valid, prop_errors = validate_property(value, properties[key])
            if not valid:
                errors.append(f"Field '{key}' invalid: {prop_errors}")

    return len(errors) == 0, errors


def validate_dataset_schema(df: pd.DataFrame, schema: Dict[str, Any], entity_name: str = "Dialogue") -> Tuple[bool, List[str]]:
    """
    Validate a pandas DataFrame against a specific entity schema.

    Args:
        df: The DataFrame to validate.
        schema: The full schema dictionary.
        entity_name: The key in the schema properties to validate against (e.g., 'Dialogue').

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []
    entity_schema = schema.get('properties', {}).get(entity_name, {})

    if not entity_schema:
        errors.append(f"Entity '{entity_name}' not found in schema")
        return False, errors

    required_fields = entity_schema.get('required', [])
    properties = entity_schema.get('properties', {})

    # Check for missing required columns
    existing_columns = set(df.columns)
    missing_columns = set(required_fields) - existing_columns
    if missing_columns:
        errors.append(f"Missing required columns: {missing_columns}")

    # Check for extra columns not in schema (optional strictness)
    # For now, we allow extra columns but log them if needed.

    # Validate data types and constraints for each column
    for col in df.columns:
        if col in properties:
            col_schema = properties[col]
            expected_type = col_schema.get('type')

            # Map pandas dtypes to JSON types
            dtype = df[col].dtype
            is_valid_type = True

            if expected_type == 'string':
                if not pd.api.types.is_string_dtype(dtype) and not pd.api.types.is_object_dtype(dtype):
                    is_valid_type = False
            elif expected_type == 'integer':
                if not pd.api.types.is_integer_dtype(dtype):
                    # Allow float if it contains only integers? No, strict check.
                    is_valid_type = False
            elif expected_type == 'number':
                if not pd.api.types.is_numeric_dtype(dtype):
                    is_valid_type = False
            elif expected_type == 'array':
                # Check if column contains lists
                if not df[col].apply(lambda x: isinstance(x, list)).all():
                    is_valid_type = False

            if not is_valid_type:
                errors.append(f"Column '{col}' has incorrect type. Expected {expected_type}, got {dtype}")

            # Check constraints (min, max, enum)
            if expected_type in ['integer', 'number']:
                if 'minimum' in col_schema:
                    if df[col].min() < col_schema['minimum']:
                        errors.append(f"Column '{col}' has values below minimum {col_schema['minimum']}")
                if 'maximum' in col_schema:
                    if df[col].max() > col_schema['maximum']:
                        errors.append(f"Column '{col}' has values above maximum {col_schema['maximum']}")
            elif expected_type == 'string' and 'enum' in col_schema:
                unique_values = df[col].dropna().unique()
                invalid_values = set(unique_values) - set(col_schema['enum'])
                if invalid_values:
                    errors.append(f"Column '{col}' has invalid enum values: {invalid_values}")

    return len(errors) == 0, errors


def validate_dataset(df: pd.DataFrame, schema_path: Optional[Union[str, Path]] = None, entity_name: str = "Dialogue") -> Tuple[bool, List[str]]:
    """
    Main entry point to validate a dataset DataFrame against the schema.

    Args:
        df: The pandas DataFrame to validate.
        schema_path: Path to the schema file.
        entity_name: The entity type to validate against.

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    schema = load_schema(schema_path)
    return validate_dataset_schema(df, schema, entity_name)


def get_missing_fields(df: pd.DataFrame, schema_path: Optional[Union[str, Path]] = None, entity_name: str = "Dialogue") -> List[str]:
    """
    Get a list of missing required fields from the DataFrame.

    Args:
        df: The DataFrame to check.
        schema_path: Path to the schema file.
        entity_name: The entity type to validate against.

    Returns:
        List of missing field names.
    """
    schema = load_schema(schema_path)
    entity_schema = schema.get('properties', {}).get(entity_name, {})
    required_fields = entity_schema.get('required', [])
    existing_columns = set(df.columns)
    return list(set(required_fields) - existing_columns)


def validate_dataset_schema_wrapper(df: pd.DataFrame, schema_path: Optional[Union[str, Path]] = None) -> bool:
    """
    Wrapper function to validate dataset schema and raise exception on failure.

    Args:
        df: The DataFrame to validate.
        schema_path: Path to the schema file.

    Raises:
        SchemaValidationError: If validation fails.
    """
    is_valid, errors = validate_dataset(df, schema_path)
    if not is_valid:
        raise SchemaValidationError(f"Schema validation failed: {'; '.join(errors)}")
    return True