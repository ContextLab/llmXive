"""
Schema validation utilities for the news-volume-anxiety pipeline.
Validates data against YAML schemas using jsonschema.
"""
import os
import sys
import logging
from typing import Dict, Any, Optional, List, Tuple
import re
import yaml
import jsonschema
from jsonschema import validate, ValidationError as JsonSchemaValidationError
from pathlib import Path

# Import logging utility from sibling module
try:
    from utils.logging import get_logger
except ImportError:
    # Fallback if running as __main__ or direct import
    def get_logger(name: str = __name__) -> logging.Logger:
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

logger = get_logger(__name__)

class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass

def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load a YAML schema file and return it as a dictionary.

    Args:
        schema_path: Path to the schema YAML file.

    Returns:
        Dictionary representation of the schema.

    Raises:
        ValidationError: If the schema file cannot be loaded or parsed.
    """
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
            if schema is None:
                raise ValidationError(f"Schema file {schema_path} is empty.")
            return schema
    except FileNotFoundError:
        raise ValidationError(f"Schema file not found: {schema_path}")
    except yaml.YAMLError as e:
        raise ValidationError(f"Failed to parse schema {schema_path}: {e}")
    except Exception as e:
        raise ValidationError(f"Unexpected error loading schema {schema_path}: {e}")

def validate_field_type(value: Any, expected_type: str) -> bool:
    """
    Validate that a value matches the expected JSON Schema type.

    Args:
        value: The value to check.
        expected_type: The expected type string (e.g., 'string', 'integer', 'number', 'boolean', 'array', 'object', 'null').

    Returns:
        True if the type matches, False otherwise.
    """
    type_map = {
        'string': str,
        'integer': int,
        'number': (int, float),
        'boolean': bool,
        'array': list,
        'object': dict,
        'null': type(None)
    }

    if expected_type not in type_map:
        logger.warning(f"Unknown type {expected_type} in schema validation.")
        return True  # Skip validation for unknown types to avoid false negatives

    expected_python_type = type_map[expected_type]
    
    # Special handling for integer/number distinction in Python
    if expected_type == 'integer' and isinstance(value, bool):
        return False # bool is a subclass of int in Python, but not an integer in JSON schema
    
    return isinstance(value, expected_python_type)

def validate_value_constraints(value: Any, constraints: Dict[str, Any]) -> bool:
    """
    Validate a value against specific constraints (min, max, pattern, etc.).

    Args:
        value: The value to check.
        constraints: Dictionary of constraints (e.g., {'minimum': 0, 'pattern': r'^[A-Z]+$'}).

    Returns:
        True if all constraints are satisfied, False otherwise.
    """
    if not isinstance(constraints, dict):
        return True

    if 'minimum' in constraints:
        if isinstance(value, (int, float)) and value < constraints['minimum']:
            return False

    if 'maximum' in constraints:
        if isinstance(value, (int, float)) and value > constraints['maximum']:
            return False

    if 'minLength' in constraints:
        if isinstance(value, str) and len(value) < constraints['minLength']:
            return False

    if 'maxLength' in constraints:
        if isinstance(value, str) and len(value) > constraints['maxLength']:
            return False

    if 'pattern' in constraints:
        if isinstance(value, str):
            if not re.match(constraints['pattern'], value):
                return False

    return True

def validate_record(record: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate a single data record against a schema.

    Args:
        record: The data record (dictionary) to validate.
        schema: The JSON Schema definition.

    Returns:
        List of error messages. Empty if valid.
    """
    errors = []
    
    # Use jsonschema for comprehensive validation
    try:
        validate(instance=record, schema=schema)
    except JsonSchemaValidationError as e:
        errors.append(f"Validation error: {e.message} at path: {e.path}")
    
    # Additional manual checks if needed (though jsonschema covers most)
    # For example, checking required fields explicitly if jsonschema doesn't catch it in a specific setup
    if 'required' in schema:
        for field in schema['required']:
            if field not in record:
                errors.append(f"Missing required field: {field}")

    return errors

def validate_dataset_file(file_path: str, schema_path: str) -> bool:
    """
    Validate a CSV dataset file against a schema.
    Reads the CSV, treats each row as a record, and validates against the schema.

    Args:
        file_path: Path to the CSV file.
        schema_path: Path to the schema YAML file.

    Returns:
        True if all records are valid, False otherwise.

    Raises:
        ValidationError: If the file or schema cannot be loaded.
    """
    import pandas as pd

    try:
        schema = load_schema(schema_path)
    except ValidationError as e:
        logger.error(f"Failed to load schema: {e}")
        raise

    if not os.path.exists(file_path):
        raise ValidationError(f"Dataset file not found: {file_path}")

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise ValidationError(f"Failed to read CSV {file_path}: {e}")

    if df.empty:
        logger.warning(f"Dataset file {file_path} is empty. Skipping validation.")
        return True

    # The schema should define 'properties' that match the CSV columns
    # We validate each row as a JSON object
    all_errors = []
    for idx, row in df.iterrows():
        record = row.to_dict()
        row_errors = validate_record(record, schema)
        if row_errors:
            all_errors.extend([f"Row {idx}: {err}" for err in row_errors])
            # Optionally break on first error or continue to collect all
            # For now, collect all
    
    if all_errors:
        logger.error(f"Validation failed for {file_path} with {len(all_errors)} errors:")
        for err in all_errors[:10]: # Log first 10
            logger.error(f"  - {err}")
        if len(all_errors) > 10:
            logger.error(f"  ... and {len(all_errors) - 10} more errors.")
        return False

    logger.info(f"Dataset {file_path} validated successfully against {schema_path}.")
    return True

def validate_output_file(file_path: str, schema_path: str) -> bool:
    """
    Validate an output file (JSON or CSV) against a schema.
    Currently supports CSV and JSON formats.

    Args:
        file_path: Path to the output file.
        schema_path: Path to the schema YAML file.

    Returns:
        True if valid, False otherwise.
    """
    if file_path.endswith('.csv'):
        return validate_dataset_file(file_path, schema_path)
    elif file_path.endswith('.json'):
        import json
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            schema = load_schema(schema_path)
            validate(instance=data, schema=schema)
            logger.info(f"Output file {file_path} validated successfully against {schema_path}.")
            return True
        except JsonSchemaValidationError as e:
            logger.error(f"Validation error in {file_path}: {e.message}")
            return False
        except Exception as e:
            raise ValidationError(f"Failed to validate output file {file_path}: {e}")
    else:
        raise ValidationError(f"Unsupported file format for validation: {file_path}")

def validate_against_schema(data: Any, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Generic validation function for any data structure against a schema.

    Args:
        data: The data to validate (dict, list, etc.).
        schema: The JSON Schema definition.

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []
    try:
        validate(instance=data, schema=schema)
        return True, []
    except JsonSchemaValidationError as e:
        errors.append(f"Validation error: {e.message} at path: {list(e.path)}")
        return False, errors

def validate_output_file_structure(file_path: str, schema_path: str) -> bool:
    """
    Alias for validate_output_file, ensuring structure matches schema.
    """
    return validate_output_file(file_path, schema_path)

def validate_dataset_file_structure(file_path: str, schema_path: str) -> bool:
    """
    Alias for validate_dataset_file, ensuring structure matches schema.
    """
    return validate_dataset_file(file_path, schema_path)

def main():
    """
    CLI entry point for schema validation.
    Usage: python -m code.utils.validation --file <path> --schema <path>
    """
    import argparse

    parser = argparse.ArgumentParser(description='Validate data files against JSON schemas.')
    parser.add_argument('--file', type=str, required=True, help='Path to the data file (CSV or JSON)')
    parser.add_argument('--schema', type=str, required=True, help='Path to the schema YAML file')
    
    args = parser.parse_args()

    try:
        if args.file.endswith('.csv'):
            success = validate_dataset_file(args.file, args.schema)
        else:
            success = validate_output_file(args.file, args.schema)
        
        if success:
            print(f"Validation passed for {args.file}")
            sys.exit(0)
        else:
            print(f"Validation failed for {args.file}")
            sys.exit(1)
    except ValidationError as e:
        print(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
