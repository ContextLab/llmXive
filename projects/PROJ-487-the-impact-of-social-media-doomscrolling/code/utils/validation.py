"""
Schema validation utilities for the llmXive science pipeline.

This module provides functions to load and validate data against
JSON Schema definitions and Pydantic models for type safety.
"""

import os
import sys
import logging
from typing import Dict, Any, Optional, List, Tuple, Union
import re
import yaml
import json
import jsonschema
from jsonschema import validate, ValidationError as JsonSchemaError, SchemaError
from pathlib import Path

# Import Pydantic models from the models module (T007c)
from utils.models import TimeSeriesRecord, AnalysisResult, validate_time_series_record, validate_analysis_result

from utils.logging import get_logger

logger = get_logger(__name__)

class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass

def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load a JSON Schema from a YAML or JSON file.

    Args:
        schema_path: Path to the schema file.

    Returns:
        Dictionary containing the schema.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        ValueError: If the file format is unsupported or parsing fails.
    """
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if schema_path.endswith('.yaml') or schema_path.endswith('.yml'):
        try:
            schema = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse YAML schema: {e}")
    elif schema_path.endswith('.json'):
        try:
            schema = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON schema: {e}")
    else:
        raise ValueError(f"Unsupported schema file format: {schema_path}")

    if not isinstance(schema, dict):
        raise ValueError("Schema must be a JSON object or YAML mapping")

    return schema

def validate_field_type(value: Any, expected_type: str) -> bool:
    """
    Validate that a value matches the expected JSON Schema type.

    Args:
        value: The value to check.
        expected_type: The expected type (string, number, integer, boolean, object, array).

    Returns:
        True if the type matches, False otherwise.
    """
    if expected_type == 'string':
        return isinstance(value, str)
    elif expected_type == 'number':
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    elif expected_type == 'integer':
        return isinstance(value, int) and not isinstance(value, bool)
    elif expected_type == 'boolean':
        return isinstance(value, bool)
    elif expected_type == 'object':
        return isinstance(value, dict)
    elif expected_type == 'array':
        return isinstance(value, list)
    elif expected_type == 'null':
        return value is None
    else:
        logger.warning(f"Unknown type expected: {expected_type}")
        return False

def validate_value_constraints(value: Any, constraints: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate that a value meets specific constraints (pattern, minimum, maximum, etc.).

    Args:
        value: The value to check.
        constraints: Dictionary of constraints from the schema.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if 'pattern' in constraints and isinstance(value, str):
        pattern = constraints['pattern']
        if not re.match(pattern, value):
            return False, f"Value '{value}' does not match pattern '{pattern}'"

    if 'minimum' in constraints:
        if value < constraints['minimum']:
            return False, f"Value {value} is less than minimum {constraints['minimum']}"

    if 'maximum' in constraints:
        if value > constraints['maximum']:
            return False, f"Value {value} is greater than maximum {constraints['maximum']}"

    if 'minLength' in constraints and isinstance(value, str):
        if len(value) < constraints['minLength']:
            return False, f"String length {len(value)} is less than minimum {constraints['minLength']}"

    if 'maxLength' in constraints and isinstance(value, str):
        if len(value) > constraints['maxLength']:
            return False, f"String length {len(value)} is greater than maximum {constraints['maxLength']}"

    if 'enum' in constraints:
        if value not in constraints['enum']:
            return False, f"Value '{value}' is not in allowed enum values: {constraints['enum']}"

    return True, ""

def validate_record(record: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a single record against a JSON Schema.

    Args:
        record: The record to validate.
        schema: The JSON Schema to validate against.

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []

    # Check required fields
    required_fields = schema.get('required', [])
    for field in required_fields:
        if field not in record:
            errors.append(f"Missing required field: {field}")

    # Validate each field in the record
    properties = schema.get('properties', {})
    for field, value in record.items():
        if field in properties:
            field_schema = properties[field]
            expected_type = field_schema.get('type')

            if expected_type and not validate_field_type(value, expected_type):
                errors.append(f"Field '{field}' has incorrect type. Expected {expected_type}, got {type(value).__name__}")
                continue

            # Check constraints
            is_valid, error_msg = validate_value_constraints(value, field_schema)
            if not is_valid:
                errors.append(f"Field '{field}': {error_msg}")

    return len(errors) == 0, errors

def validate_against_schema(data: Union[Dict[str, Any], List[Dict[str, Any]]], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate data against a JSON Schema using the jsonschema library.

    Args:
        data: The data to validate (single record or list of records).
        schema: The JSON Schema to validate against.

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    try:
        if isinstance(data, list):
            for i, record in enumerate(data):
                validate(instance=record, schema=schema)
        else:
            validate(instance=data, schema=schema)
        return True, []
    except JsonSchemaError as e:
        return False, [str(e)]
    except Exception as e:
        return False, [f"Unexpected error during validation: {str(e)}"]

def validate_with_pydantic(data: Dict[str, Any], model_class: Any) -> Tuple[bool, Optional[Any], List[str]]:
    """
    Validate data using a Pydantic model for type safety.

    Args:
        data: The data to validate.
        model_class: The Pydantic model class to use.

    Returns:
        Tuple of (is_valid, validated_model_instance_or_none, list_of_errors).
    """
    try:
        instance = model_class(**data)
        return True, instance, []
    except Exception as e:
        # Pydantic raises ValidationError which contains detailed error messages
        errors = []
        if hasattr(e, 'errors'):
            for err in e.errors():
                errors.append(f"Field '{err.get('loc', ['unknown'])[0]}': {err.get('msg', 'Unknown error')}")
        else:
            errors.append(str(e))
        return False, None, errors

def validate_dataset_file(file_path: str, schema_path: str, pydantic_model: Any = None) -> Dict[str, Any]:
    """
    Validate a dataset CSV file against a schema and optionally a Pydantic model.

    Args:
        file_path: Path to the CSV file.
        schema_path: Path to the JSON Schema file.
        pydantic_model: Optional Pydantic model class for additional type validation.

    Returns:
        Dictionary with validation results.
    """
    import pandas as pd

    result = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'records_validated': 0,
        'records_failed': 0,
        'schema_validation': True,
        'pydantic_validation': True
    }

    if not os.path.exists(file_path):
        result['valid'] = False
        result['errors'].append(f"File not found: {file_path}")
        return result

    if not os.path.exists(schema_path):
        result['valid'] = False
        result['errors'].append(f"Schema file not found: {schema_path}")
        return result

    try:
        schema = load_schema(schema_path)
    except Exception as e:
        result['valid'] = False
        result['errors'].append(f"Failed to load schema: {str(e)}")
        return result

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        result['valid'] = False
        result['errors'].append(f"Failed to read CSV file: {str(e)}")
        return result

    if df.empty:
        result['warnings'].append("CSV file is empty")
        return result

    # Convert DataFrame to list of dicts
    records = df.to_dict('records')

    # Validate each record against JSON Schema
    for i, record in enumerate(records):
        is_valid, errors = validate_record(record, schema)
        if not is_valid:
            result['valid'] = False
            result['schema_validation'] = False
            result['records_failed'] += 1
            for error in errors:
                result['errors'].append(f"Record {i}: {error}")
        else:
            result['records_validated'] += 1

    # Validate against Pydantic model if provided
    if pydantic_model:
        for i, record in enumerate(records):
            is_valid, instance, errors = validate_with_pydantic(record, pydantic_model)
            if not is_valid:
                result['valid'] = False
                result['pydantic_validation'] = False
                result['records_failed'] += 1
                for error in errors:
                    result['errors'].append(f"Record {i} (Pydantic): {error}")
            else:
                result['records_validated'] += 1

    return result

def validate_output_file_structure(file_path: str, schema_path: str, pydantic_model: Any = None) -> Dict[str, Any]:
    """
    Validate an output file (e.g., analysis results) against a schema and optionally a Pydantic model.

    Args:
        file_path: Path to the output file (CSV or JSON).
        schema_path: Path to the JSON Schema file.
        pydantic_model: Optional Pydantic model class for additional type validation.

    Returns:
        Dictionary with validation results.
    """
    import pandas as pd
    import json

    result = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'records_validated': 0,
        'records_failed': 0,
        'schema_validation': True,
        'pydantic_validation': True
    }

    if not os.path.exists(file_path):
        result['valid'] = False
        result['errors'].append(f"File not found: {file_path}")
        return result

    if not os.path.exists(schema_path):
        result['valid'] = False
        result['errors'].append(f"Schema file not found: {schema_path}")
        return result

    try:
        schema = load_schema(schema_path)
    except Exception as e:
        result['valid'] = False
        result['errors'].append(f"Failed to load schema: {str(e)}")
        return result

    # Determine file type and load data
    try:
        if file_path.endswith('.json'):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        elif file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
            data = df.to_dict('records')
        else:
            result['valid'] = False
            result['errors'].append(f"Unsupported file format: {file_path}")
            return result
    except Exception as e:
        result['valid'] = False
        result['errors'].append(f"Failed to read file: {str(e)}")
        return result

    if isinstance(data, dict):
        data = [data]

    if not data:
        result['warnings'].append("File is empty")
        return result

    # Validate each record
    for i, record in enumerate(data):
        is_valid, errors = validate_record(record, schema)
        if not is_valid:
            result['valid'] = False
            result['schema_validation'] = False
            result['records_failed'] += 1
            for error in errors:
                result['errors'].append(f"Record {i}: {error}")
        else:
            result['records_validated'] += 1

    # Validate against Pydantic model if provided
    if pydantic_model:
        for i, record in enumerate(data):
            is_valid, instance, errors = validate_with_pydantic(record, pydantic_model)
            if not is_valid:
                result['valid'] = False
                result['pydantic_validation'] = False
                result['records_failed'] += 1
                for error in errors:
                    result['errors'].append(f"Record {i} (Pydantic): {error}")
            else:
                result['records_validated'] += 1

    return result

def main():
    """
    Main function to demonstrate validation usage.
    This script can be run to validate specific files if paths are provided.
    """
    import argparse

    parser = argparse.ArgumentParser(description='Validate data files against schemas and Pydantic models.')
    parser.add_argument('--dataset', type=str, help='Path to dataset CSV file')
    parser.add_argument('--output', type=str, help='Path to output file (CSV or JSON)')
    parser.add_argument('--schema-dataset', type=str, default='code/contracts/dataset.schema.yaml', help='Path to dataset schema')
    parser.add_argument('--schema-output', type=str, default='code/contracts/output.schema.yaml', help='Path to output schema')

    args = parser.parse_args()

    if not args.dataset and not args.output:
        print("Usage: python -m utils.validation --dataset <path> or --output <path>")
        sys.exit(1)

    if args.dataset:
        logger.info(f"Validating dataset file: {args.dataset}")
        result = validate_dataset_file(args.dataset, args.schema_dataset, TimeSeriesRecord)
        if result['valid']:
            logger.info(f"Validation PASSED: {result['records_validated']} records validated successfully.")
        else:
            logger.error(f"Validation FAILED: {len(result['errors'])} errors found.")
            for error in result['errors']:
                logger.error(f"  - {error}")
        sys.exit(0 if result['valid'] else 1)

    if args.output:
        logger.info(f"Validating output file: {args.output}")
        result = validate_output_file_structure(args.output, args.schema_output, AnalysisResult)
        if result['valid']:
            logger.info(f"Validation PASSED: {result['records_validated']} records validated successfully.")
        else:
            logger.error(f"Validation FAILED: {len(result['errors'])} errors found.")
            for error in result['errors']:
                logger.error(f"  - {error}")
        sys.exit(0 if result['valid'] else 1)

if __name__ == '__main__':
    main()