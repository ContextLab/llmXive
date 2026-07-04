"""
Schema validation utilities for the llmXive automated science pipeline.

This module provides functions to validate data files against YAML schema definitions
using the pyyaml library. It supports validating both input datasets and output files.
"""

import os
import sys
from typing import Dict, Any, Optional, List, Tuple
import yaml

from utils.logging import get_logger

logger = get_logger(__name__)

# Default schema file paths relative to project root
DATASET_SCHEMA_PATH = "contracts/dataset.schema.yaml"
OUTPUT_SCHEMA_PATH = "contracts/output.schema.yaml"


def load_schema(schema_path: str) -> Optional[Dict[str, Any]]:
    """
    Load a YAML schema definition from a file.

    Args:
        schema_path: Relative path to the schema YAML file.

    Returns:
        Dictionary containing the schema definition, or None if loading fails.
    """
    try:
        # Resolve relative to project root (assumed current working directory)
        full_path = os.path.join(os.getcwd(), schema_path)
        
        if not os.path.exists(full_path):
            logger.error(f"Schema file not found: {full_path}")
            return None

        with open(full_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        
        if schema is None:
            logger.error(f"Schema file is empty or invalid YAML: {full_path}")
            return None

        logger.info(f"Successfully loaded schema: {schema_path}")
        return schema

    except yaml.YAMLError as e:
        logger.error(f"YAML parsing error in {schema_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading schema {schema_path}: {e}")
        return None


def validate_field_type(value: Any, expected_type: str) -> bool:
    """
    Validate that a value matches the expected type string.

    Supported types: string, integer, float, boolean, list, dict, any

    Args:
        value: The value to check.
        expected_type: String representation of the expected type.

    Returns:
        True if the value matches the type, False otherwise.
    """
    type_mapping = {
        'string': str,
        'str': str,
        'integer': int,
        'int': int,
        'float': float,
        'number': (int, float),
        'boolean': bool,
        'bool': bool,
        'list': list,
        'array': list,
        'dict': dict,
        'object': dict,
        'any': None,  # Any type is always valid
    }

    if expected_type.lower() == 'any':
        return True

    expected_python_type = type_mapping.get(expected_type.lower())
    
    if expected_python_type is None:
        logger.warning(f"Unknown type specification: {expected_type}")
        return True  # Be permissive for unknown types

    # Special case: allow integers to pass as floats
    if expected_python_type == float and isinstance(value, int) and not isinstance(value, bool):
        return True

    return isinstance(value, expected_python_type)


def validate_value_constraints(value: Any, constraints: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate a value against specified constraints.

    Args:
        value: The value to check.
        constraints: Dictionary of constraint key-value pairs.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if 'min' in constraints:
        if value < constraints['min']:
            return False, f"Value {value} is less than minimum {constraints['min']}"

    if 'max' in constraints:
        if value > constraints['max']:
            return False, f"Value {value} is greater than maximum {constraints['max']}"

    if 'min_length' in constraints and isinstance(value, (str, list)):
        if len(value) < constraints['min_length']:
            return False, f"Length {len(value)} is less than minimum {constraints['min_length']}"

    if 'max_length' in constraints and isinstance(value, (str, list)):
        if len(value) > constraints['max_length']:
            return False, f"Length {len(value)} is greater than maximum {constraints['max_length']}"

    if 'pattern' in constraints and isinstance(value, str):
        import re
        if not re.match(constraints['pattern'], value):
            return False, f"Value '{value}' does not match pattern '{constraints['pattern']}'"

    if 'enum' in constraints:
        if value not in constraints['enum']:
            return False, f"Value '{value}' is not in allowed values: {constraints['enum']}"

    return True, ""


def validate_record(record: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a single record (row) against a schema definition.

    Args:
        record: Dictionary representing a data record.
        schema: Schema definition dictionary.

    Returns:
        Tuple of (is_valid, list_of_error_messages).
    """
    errors = []
    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})

    # Check required fields
    for field in required_fields:
        if field not in record:
            errors.append(f"Missing required field: {field}")

    # Validate each field present in the record
    for field_name, field_value in record.items():
        if field_name not in properties:
            # Unknown field - log warning but don't fail (permissive mode)
            logger.warning(f"Unknown field '{field_name}' in record, skipping validation")
            continue

        field_spec = properties[field_name]
        
        # Type validation
        expected_type = field_spec.get('type', 'any')
        if not validate_field_type(field_value, expected_type):
            errors.append(f"Field '{field_name}' has invalid type. Expected {expected_type}, got {type(field_value).__name__}")
            continue

        # Constraint validation
        constraints = field_spec.get('constraints', {})
        if constraints:
            is_valid, error_msg = validate_value_constraints(field_value, constraints)
            if not is_valid:
                errors.append(f"Field '{field_name}': {error_msg}")

    return len(errors) == 0, errors


def validate_dataset_file(file_path: str, schema_path: str = DATASET_SCHEMA_PATH) -> Tuple[bool, List[str]]:
    """
    Validate a dataset file (CSV/JSON) against a schema.

    For CSV files, this validates the header and a sample of rows.
    For JSON files, this validates the structure.

    Args:
        file_path: Path to the data file.
        schema_path: Path to the schema definition.

    Returns:
        Tuple of (is_valid, list_of_error_messages).
    """
    import pandas as pd

    if not os.path.exists(file_path):
        return False, [f"Data file not found: {file_path}"]

    schema = load_schema(schema_path)
    if schema is None:
        return False, [f"Failed to load schema: {schema_path}"]

    try:
        # Determine file type and load
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
            records = df.to_dict('records')
        elif file_path.endswith('.json'):
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    records = data
                elif isinstance(data, dict):
                    # Assume the data is under a specific key or the dict itself is the record
                    records = [data]
                else:
                    return False, ["Invalid JSON structure: expected list or object"]
        else:
            return False, [f"Unsupported file format: {file_path}. Use .csv or .json"]

        if not records:
            return False, ["Data file is empty"]

        # Validate all records
        all_errors = []
        for i, record in enumerate(records):
            is_valid, errors = validate_record(record, schema)
            if not is_valid:
                all_errors.extend([f"Record {i}: {err}" for err in errors])

            # Limit error reporting to first 10 errors for readability
            if len(all_errors) >= 10:
                all_errors.append("... (additional errors truncated)")
                break

        if all_errors:
            return False, all_errors

        logger.info(f"Dataset validation passed: {file_path}")
        return True, []

    except Exception as e:
        return False, [f"Error processing data file: {str(e)}"]


def validate_output_file(file_path: str, schema_path: str = OUTPUT_SCHEMA_PATH) -> Tuple[bool, List[str]]:
    """
    Validate an output file against the output schema.

    Args:
        file_path: Path to the output file.
        schema_path: Path to the output schema definition.

    Returns:
        Tuple of (is_valid, list_of_error_messages).
    """
    return validate_dataset_file(file_path, schema_path)


def validate_against_schema(
    file_path: str,
    schema_type: str = 'dataset',
    custom_schema_path: Optional[str] = None
) -> bool:
    """
    Main entry point for validating a file against a schema.

    Args:
        file_path: Path to the file to validate.
        schema_type: Either 'dataset' or 'output'.
        custom_schema_path: Optional custom schema path.

    Returns:
        True if validation passes, False otherwise.
    """
    if schema_type == 'dataset':
        schema_path = custom_schema_path or DATASET_SCHEMA_PATH
    elif schema_type == 'output':
        schema_path = custom_schema_path or OUTPUT_SCHEMA_PATH
    else:
        logger.error(f"Unknown schema type: {schema_type}")
        return False

    is_valid, errors = validate_dataset_file(file_path, schema_path)

    if not is_valid:
        logger.error(f"Validation failed for {file_path}:")
        for err in errors[:5]:  # Log first 5 errors
            logger.error(f"  - {err}")
        if len(errors) > 5:
            logger.error(f"  ... and {len(errors) - 5} more errors")
    
    return is_valid


if __name__ == "__main__":
    # Simple CLI for testing validation
    if len(sys.argv) < 2:
        print("Usage: python validation.py <file_path> [schema_type]")
        print("  schema_type: 'dataset' (default) or 'output'")
        sys.exit(1)

    target_file = sys.argv[1]
    schema_type = sys.argv[2] if len(sys.argv) > 2 else 'dataset'

    if validate_against_schema(target_file, schema_type):
        print(f"✓ Validation passed for {target_file}")
        sys.exit(0)
    else:
        print(f"✗ Validation failed for {target_file}")
        sys.exit(1)
