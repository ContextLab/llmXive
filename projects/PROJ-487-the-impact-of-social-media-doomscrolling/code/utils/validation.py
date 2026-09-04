"""
Schema validation utilities for the llmXive research pipeline.

This module provides functions to load and validate data against
JSON schemas defined in the contracts directory.
"""
import os
import sys
import logging
from typing import Dict, Any, Optional, List, Tuple, Union
import re
import yaml
import json
import pandas as pd

try:
    import jsonschema
    from jsonschema import validate, ValidationError as JsonSchemaValidationError, Draft7Validator
except ImportError:
    # Fallback if jsonschema is not installed (should be in requirements.txt)
    print("Error: jsonschema library is required. Install with: pip install jsonschema")
    sys.exit(1)

# Configure logger
logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass

def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load a JSON schema from a YAML file.
    
    Args:
        schema_path: Path to the schema file (YAML format)
        
    Returns:
        Dictionary containing the schema
        
    Raises:
        FileNotFoundError: If schema file doesn't exist
        yaml.YAMLError: If YAML parsing fails
    """
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)
    
    logger.info(f"Loaded schema from {schema_path}")
    return schema

def validate_field_type(value: Any, expected_type: str, field_name: str) -> bool:
    """
    Validate that a value matches the expected JSON Schema type.
    
    Args:
        value: The value to validate
        expected_type: Expected type string (e.g., 'string', 'number', 'integer')
        field_name: Name of the field for error messages
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If type mismatch
    """
    type_mapping = {
        'string': str,
        'number': (int, float),
        'integer': int,
        'boolean': bool,
        'array': list,
        'object': dict,
        'null': type(None)
    }
    
    if expected_type not in type_mapping:
        logger.warning(f"Unknown type '{expected_type}' for field '{field_name}'")
        return True
    
    expected_python_type = type_mapping[expected_type]
    
    # Special handling for number vs integer
    if expected_type == 'number':
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValidationError(
                f"Field '{field_name}' must be a number, got {type(value).__name__}"
            )
    elif expected_type == 'integer':
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValidationError(
                f"Field '{field_name}' must be an integer, got {type(value).__name__}"
            )
    else:
        if not isinstance(value, expected_python_type):
            raise ValidationError(
                f"Field '{field_name}' must be {expected_type}, got {type(value).__name__}"
            )
    
    return True

def validate_value_constraints(value: Any, constraints: Dict[str, Any], field_name: str) -> bool:
    """
    Validate value against constraints like pattern, minimum, maximum, etc.
    
    Args:
        value: The value to validate
        constraints: Dictionary of constraints from schema
        field_name: Name of the field for error messages
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If constraints not met
    """
    # Pattern validation for strings
    if 'pattern' in constraints and isinstance(value, str):
        pattern = constraints['pattern']
        if not re.match(pattern, value):
            raise ValidationError(
                f"Field '{field_name}' value '{value}' does not match pattern '{pattern}'"
            )
    
    # Minimum/Maximum for numbers
    if 'minimum' in constraints and isinstance(value, (int, float)):
        if value < constraints['minimum']:
            raise ValidationError(
                f"Field '{field_name}' value {value} is less than minimum {constraints['minimum']}"
            )
    
    if 'maximum' in constraints and isinstance(value, (int, float)):
        if value > constraints['maximum']:
            raise ValidationError(
                f"Field '{field_name}' value {value} is greater than maximum {constraints['maximum']}"
            )
    
    # Enum validation
    if 'enum' in constraints:
        if value not in constraints['enum']:
            raise ValidationError(
                f"Field '{field_name}' value '{value}' not in allowed values: {constraints['enum']}"
            )
    
    # MinLength/MaxLength for strings
    if 'minLength' in constraints and isinstance(value, str):
        if len(value) < constraints['minLength']:
            raise ValidationError(
                f"Field '{field_name}' length {len(value)} is less than minimum {constraints['minLength']}"
            )
    
    if 'maxLength' in constraints and isinstance(value, str):
        if len(value) > constraints['maxLength']:
            raise ValidationError(
                f"Field '{field_name}' length {len(value)} is greater than maximum {constraints['maxLength']}"
            )
    
    return True

def validate_record(record: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate a single record against a schema.
    
    Args:
        record: Dictionary representing a single data record
        schema: JSON Schema definition
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    properties = schema.get('properties', {})
    required = schema.get('required', [])
    
    # Check required fields
    for field in required:
        if field not in record:
            errors.append(f"Missing required field: '{field}'")
    
    # Validate each field
    for field_name, field_value in record.items():
        if field_name not in properties:
            if schema.get('additionalProperties') is False:
                errors.append(f"Additional property not allowed: '{field_name}'")
            continue
        
        field_schema = properties[field_name]
        
        # Type validation
        try:
            if 'type' in field_schema:
                validate_field_type(field_value, field_schema['type'], field_name)
        except ValidationError as e:
            errors.append(str(e))
        
        # Constraint validation
        try:
            validate_value_constraints(field_value, field_schema, field_name)
        except ValidationError as e:
            errors.append(str(e))
    
    return errors

def validate_dataset_file(
    file_path: str, 
    schema_path: str, 
    date_column: str = 'date',
    value_column: str = 'value'
) -> Tuple[bool, List[str]]:
    """
    Validate a CSV dataset file against a schema.
    
    Args:
        file_path: Path to the CSV file
        schema_path: Path to the schema YAML file
        date_column: Name of the date column (for additional validation)
        value_column: Name of the value column (for additional validation)
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    try:
        schema = load_schema(schema_path)
    except Exception as e:
        return False, [f"Failed to load schema: {str(e)}"]
    
    if not os.path.exists(file_path):
        return False, [f"Data file not found: {file_path}"]
    
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        return False, [f"Failed to read CSV file: {str(e)}"]
    
    errors = []
    records_validated = 0
    
    # Convert DataFrame to list of dicts for validation
    for idx, row in df.iterrows():
        record = row.to_dict()
        record_errors = validate_record(record, schema)
        
        if record_errors:
            errors.extend([f"Row {idx + 2}: {err}" for err in record_errors])
        
        records_validated += 1
        
        # Log progress for large files
        if records_validated % 1000 == 0:
            logger.info(f"Validated {records_validated} records...")
    
    is_valid = len(errors) == 0
    
    if is_valid:
        logger.info(f"Dataset validation passed: {records_validated} records validated")
    else:
        logger.error(f"Dataset validation failed with {len(errors)} errors")
    
    return is_valid, errors

def validate_output_file_structure(
    file_path: str,
    schema_path: str
) -> Tuple[bool, List[str]]:
    """
    Validate an output CSV file (e.g., analysis results) against a schema.
    
    Args:
        file_path: Path to the output CSV file
        schema_path: Path to the schema YAML file
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    return validate_dataset_file(file_path, schema_path)

def validate_against_schema(
    data: Union[Dict[str, Any], List[Dict[str, Any]], pd.DataFrame],
    schema: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    Generic validation function using jsonschema library.
    
    Args:
        data: Data to validate (dict, list of dicts, or DataFrame)
        schema: JSON Schema definition
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    try:
        if isinstance(data, pd.DataFrame):
            # Convert DataFrame to list of dicts
            data_list = data.to_dict('records')
            for record in data_list:
                try:
                    validate(record, schema)
                except JsonSchemaValidationError as e:
                    errors.append(f"Validation error: {e.message}")
        elif isinstance(data, list):
            for record in data:
                try:
                    validate(record, schema)
                except JsonSchemaValidationError as e:
                    errors.append(f"Validation error: {e.message}")
        elif isinstance(data, dict):
            try:
                validate(data, schema)
            except JsonSchemaValidationError as e:
                errors.append(f"Validation error: {e.message}")
        else:
            errors.append(f"Unsupported data type: {type(data)}")
    except Exception as e:
        errors.append(f"Validation process failed: {str(e)}")
    
    return len(errors) == 0, errors

def main():
    """
    Command-line interface for schema validation.
    
    Usage:
        python -m utils.validation --data <path> --schema <path> [--type dataset|output]
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate data against JSON schema')
    parser.add_argument('--data', required=True, help='Path to data file (CSV)')
    parser.add_argument('--schema', required=True, help='Path to schema file (YAML)')
    parser.add_argument('--type', choices=['dataset', 'output'], default='dataset',
                      help='Type of validation (dataset or output)')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)
    
    # Determine validation function based on type
    if args.type == 'dataset':
        is_valid, errors = validate_dataset_file(args.data, args.schema)
    else:
        is_valid, errors = validate_output_file_structure(args.data, args.schema)
    
    if is_valid:
        print("Validation PASSED")
        sys.exit(0)
    else:
        print("Validation FAILED")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

if __name__ == '__main__':
    main()