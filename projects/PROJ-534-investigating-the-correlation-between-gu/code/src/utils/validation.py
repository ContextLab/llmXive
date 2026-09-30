"""
Validation utilities to enforce schema contracts.

This module provides functions to validate dataframes and dictionaries
against schema definitions defined in contracts/*.yaml files.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import pandas as pd
import numpy as np
import yaml

from code.src.utils.config import get_project_root

logger = logging.getLogger(__name__)


def load_schema(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a schema definition from a YAML file.

    Args:
        schema_path: Path to the schema YAML file.

    Returns:
        Dictionary containing the schema definition.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the YAML file is malformed.
    """
    schema_path = Path(schema_path)
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)

    logger.debug(f"Loaded schema from {schema_path}")
    return schema


def validate_field_type(value: Any, expected_type: str, field_name: str) -> bool:
    """
    Validate that a value matches the expected type.

    Args:
        value: The value to validate.
        expected_type: The expected type as a string (e.g., 'str', 'int', 'float', 'bool', 'array').
        field_name: Name of the field for error reporting.

    Returns:
        True if the type matches, False otherwise.
    """
    if pd.isna(value):
        # Null values are handled separately by required field checks
        return True

    type_mapping = {
        'str': (str,),
        'int': (int, np.integer),
        'float': (float, np.floating),
        'bool': (bool, np.bool_),
        'array': (list, tuple, np.ndarray),
    }

    if expected_type not in type_mapping:
        logger.warning(f"Unknown type '{expected_type}' for field '{field_name}', skipping type check")
        return True

    expected_types = type_mapping[expected_type]

    if isinstance(value, expected_types):
        return True

    # Special handling for numeric types that might be stored as strings in CSV
    if expected_type in ('int', 'float'):
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    logger.debug(f"Type mismatch for field '{field_name}': expected {expected_type}, got {type(value)}")
    return False


def validate_enum(value: Any, allowed_values: List[Any], field_name: str) -> bool:
    """
    Validate that a value is in the allowed enum values.

    Args:
        value: The value to validate.
        allowed_values: List of allowed values.
        field_name: Name of the field for error reporting.

    Returns:
        True if the value is in the allowed list, False otherwise.
    """
    if pd.isna(value):
        # Null values are handled separately by required field checks
        return True

    # Convert to string for comparison if needed
    if isinstance(allowed_values[0], str):
        value_str = str(value)
        allowed_str = [str(v) for v in allowed_values]
        return value_str in allowed_str

    return value in allowed_values


def validate_range(value: Any, constraints: Dict[str, Any], field_name: str) -> bool:
    """
    Validate that a numeric value is within specified constraints.

    Args:
        value: The value to validate.
        constraints: Dictionary with 'min' and/or 'max' keys.
        field_name: Name of the field for error reporting.

    Returns:
        True if the value is within constraints, False otherwise.
    """
    if pd.isna(value):
        return True

    try:
        num_value = float(value)
    except (ValueError, TypeError):
        logger.debug(f"Cannot convert value to float for range check: {value}")
        return False

    if 'min' in constraints and num_value < constraints['min']:
        logger.debug(f"Value {num_value} for '{field_name}' is below minimum {constraints['min']}")
        return False

    if 'max' in constraints and num_value > constraints['max']:
        logger.debug(f"Value {num_value} for '{field_name}' is above maximum {constraints['max']}")
        return False

    return True


def validate_dataframe_against_schema(
    df: pd.DataFrame,
    schema: Dict[str, Any],
    schema_name: str = "schema"
) -> List[Dict[str, Any]]:
    """
    Validate a dataframe against a schema definition.

    Args:
        df: The dataframe to validate.
        schema: The schema definition dictionary.
        schema_name: Name of the schema for error reporting.

    Returns:
        List of validation error dictionaries. Each error contains:
            - field: The field name that failed validation
            - row: The row index where the error occurred
            - error_type: Type of validation error ('type', 'enum', 'range', 'required', 'null')
            - message: Human-readable error message
    """
    errors = []

    if 'entities' not in schema:
        logger.warning(f"Schema '{schema_name}' does not contain 'entities' key")
        return errors

    # Assume first entity for now (single entity schema)
    entity_name = list(schema['entities'].keys())[0]
    entity_def = schema['entities'][entity_name]
    fields = entity_def.get('fields', {})

    required_fields = [
        field_name for field_name, field_def in fields.items()
        if field_def.get('required', False)
    ]

    # Check for required columns
    missing_columns = [col for col in required_fields if col not in df.columns]
    if missing_columns:
        error_msg = f"Missing required columns: {missing_columns}"
        logger.error(f"Validation failed for '{schema_name}': {error_msg}")
        errors.append({
            'field': 'columns',
            'row': -1,
            'error_type': 'required',
            'message': error_msg
        })
        return errors

    # Validate each row
    for idx, row in df.iterrows():
        for field_name, field_def in fields.items():
            if field_name not in row.index:
                continue

            value = row[field_name]

            # Check required fields for null values
            if field_def.get('required', False) and pd.isna(value):
                errors.append({
                    'field': field_name,
                    'row': int(idx),
                    'error_type': 'null',
                    'message': f"Required field '{field_name}' is null at row {idx}"
                })
                continue

            # Skip type validation for null values
            if pd.isna(value):
                continue

            # Type validation
            if 'type' in field_def:
                if not validate_field_type(value, field_def['type'], field_name):
                    errors.append({
                        'field': field_name,
                        'row': int(idx),
                        'error_type': 'type',
                        'message': f"Field '{field_name}' at row {idx} has invalid type. Expected {field_def['type']}, got {type(value)}"
                    })

            # Enum validation
            if 'enum' in field_def:
                if not validate_enum(value, field_def['enum'], field_name):
                    errors.append({
                        'field': field_name,
                        'row': int(idx),
                        'error_type': 'enum',
                        'message': f"Field '{field_name}' at row {idx} has value '{value}' not in allowed values: {field_def['enum']}"
                    })

            # Range validation
            if 'constraints' in field_def:
                if not validate_range(value, field_def['constraints'], field_name):
                    errors.append({
                        'field': field_name,
                        'row': int(idx),
                        'error_type': 'range',
                        'message': f"Field '{field_name}' at row {idx} is out of valid range"
                    })

    return errors


def validate_dataset(
    data_path: Union[str, Path],
    schema_path: Union[str, Path],
    schema_name: str = "dataset"
) -> bool:
    """
    Validate a dataset file against a schema.

    Args:
        data_path: Path to the dataset file (CSV).
        schema_path: Path to the schema YAML file.
        schema_name: Name of the schema for logging.

    Returns:
        True if validation passes, False otherwise.
    """
    data_path = Path(data_path)
    schema_path = Path(schema_path)

    logger.info(f"Validating dataset '{data_path}' against schema '{schema_path}'")

    try:
        df = pd.read_csv(data_path)
        schema = load_schema(schema_path)
    except Exception as e:
        logger.error(f"Failed to load data or schema: {e}")
        return False

    errors = validate_dataframe_against_schema(df, schema, schema_name)

    if errors:
        error_count = len(errors)
        logger.error(f"Validation failed for '{schema_name}': {error_count} error(s) found")
        for error in errors[:10]:  # Log first 10 errors
            logger.error(f"  - {error['error_type']}: {error['message']}")
        if error_count > 10:
            logger.error(f"  ... and {error_count - 10} more errors")
        return False

    logger.info(f"Validation passed for '{schema_name}': {len(df)} rows validated successfully")
    return True


def validate_result_against_analysis_schema(
    result: Dict[str, Any],
    schema_path: Union[str, Path]
) -> bool:
    """
    Validate a single analysis result dictionary against the analysis output schema.

    Args:
        result: The result dictionary to validate.
        schema_path: Path to the analysis output schema YAML file.

    Returns:
        True if validation passes, False otherwise.
    """
    schema_path = Path(schema_path)

    try:
        schema = load_schema(schema_path)
    except Exception as e:
        logger.error(f"Failed to load analysis schema: {e}")
        return False

    if 'entities' not in schema:
        logger.warning("Analysis schema does not contain 'entities' key")
        return False

    entity_name = list(schema['entities'].keys())[0]
    entity_def = schema['entities'][entity_name]
    fields = entity_def.get('fields', {})

    required_fields = [
        field_name for field_name, field_def in fields.items()
        if field_def.get('required', False)
    ]

    # Check required fields
    for field_name in required_fields:
        if field_name not in result:
            logger.error(f"Missing required field '{field_name}' in analysis result")
            return False

        value = result[field_name]
        if pd.isna(value) and field_name not in ('confidence_interval',):
            logger.error(f"Required field '{field_name}' is null in analysis result")
            return False

    # Validate types
    for field_name, field_def in fields.items():
        if field_name not in result:
            continue

        value = result[field_name]

        if 'type' in field_def:
            if not validate_field_type(value, field_def['type'], field_name):
                logger.error(f"Invalid type for field '{field_name}': expected {field_def['type']}, got {type(value)}")
                return False

        # Special validation for confidence_interval (should be a list of 2 floats)
        if field_name == 'confidence_interval':
            if not isinstance(value, (list, tuple)) or len(value) != 2:
                logger.error(f"Field 'confidence_interval' must be a list/tuple of 2 elements")
                return False
            try:
                float(value[0])
                float(value[1])
            except (ValueError, TypeError):
                logger.error(f"Field 'confidence_interval' elements must be numeric")
                return False

    return True


def main():
    """
    Main function to run validation from command line.
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='Validate dataset against schema')
    parser.add_argument('--data', type=str, required=True, help='Path to dataset CSV file')
    parser.add_argument('--schema', type=str, required=True, help='Path to schema YAML file')
    parser.add_argument('--schema-name', type=str, default='dataset', help='Name of the schema for logging')
    parser.add_argument('--log-level', type=str, default='INFO', help='Logging level')

    args = parser.parse_args()

    # Setup logging
    log_level = getattr(logging, args.log_level.upper())
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')

    success = validate_dataset(args.data, args.schema, args.schema_name)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()