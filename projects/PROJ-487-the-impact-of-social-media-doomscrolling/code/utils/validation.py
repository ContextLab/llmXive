"""
Schema validation utilities for the llmXive science pipeline.

This module provides functions to load JSON/YAML schemas and validate
data records, datasets, and output structures against them using the
`jsonschema` library.
"""
import os
import sys
import logging
from typing import Dict, Any, Optional, List, Tuple, Union
import re
import yaml
import json
import pandas as pd

# Import jsonschema dynamically to handle potential missing dependency gracefully
try:
    import jsonschema
    from jsonschema import validate, ValidationError as JsonSchemaValidationError, Draft7Validator
except ImportError:
    # Fallback for environments where jsonschema might not be installed yet
    # The main() function will handle the actual error if it's required.
    jsonschema = None
    JsonSchemaValidationError = Exception

# Configure logger
logger = logging.getLogger(__name__)

# Define base paths relative to project root
# We assume the script is run from the project root or code/
# The schemas are in specs/001-news-volume-anxiety/contracts/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SPECS_DIR = os.path.join(PROJECT_ROOT, 'specs', '001-news-volume-anxiety')
CONTRACTS_DIR = os.path.join(SPECS_DIR, 'contracts')

DATASET_SCHEMA_PATH = os.path.join(CONTRACTS_DIR, 'dataset.schema.yaml')
OUTPUT_SCHEMA_PATH = os.path.join(CONTRACTS_DIR, 'output.schema.yaml')


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load a schema from a YAML or JSON file.

    Args:
        schema_path: Path to the schema file.

    Returns:
        The schema as a dictionary.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        ValueError: If the file cannot be parsed.
    """
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            # Try YAML first, then JSON if YAML fails (though we expect YAML)
            if schema_path.endswith('.yaml') or schema_path.endswith('.yml'):
                return yaml.safe_load(f)
            else:
                return json.load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse YAML schema {schema_path}: {e}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON schema {schema_path}: {e}")


def validate_field_type(value: Any, expected_type: str) -> bool:
    """
    Validate if a value matches the expected JSON Schema type.

    Args:
        value: The value to check.
        expected_type: The expected type string (e.g., 'string', 'number', 'integer').

    Returns:
        True if valid, False otherwise.
    """
    if expected_type == 'string':
        return isinstance(value, str)
    elif expected_type == 'number':
        # In Python, int is a subset of number, but jsonschema treats them distinctively
        # unless 'integer' is not specified. Here we allow int or float for 'number'.
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    elif expected_type == 'integer':
        return isinstance(value, int) and not isinstance(value, bool)
    elif expected_type == 'boolean':
        return isinstance(value, bool)
    elif expected_type == 'array':
        return isinstance(value, list)
    elif expected_type == 'object':
        return isinstance(value, dict)
    elif expected_type == 'null':
        return value is None
    return False


def validate_value_constraints(value: Any, constraints: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate a value against specific constraints (pattern, minimum, maximum, etc.).

    Args:
        value: The value to check.
        constraints: Dictionary of constraints from the schema.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not constraints:
        return True, ""

    # Pattern check for strings
    if 'pattern' in constraints and isinstance(value, str):
        if not re.match(constraints['pattern'], value):
            return False, f"Value '{value}' does not match pattern '{constraints['pattern']}'"

    # Minimum/Maximum for numbers
    if 'minimum' in constraints and isinstance(value, (int, float)):
        if value < constraints['minimum']:
            return False, f"Value {value} is less than minimum {constraints['minimum']}"

    if 'maximum' in constraints and isinstance(value, (int, float)):
        if value > constraints['maximum']:
            return False, f"Value {value} is greater than maximum {constraints['maximum']}"

    # MinLength/MaxLength for strings
    if 'minLength' in constraints and isinstance(value, str):
        if len(value) < constraints['minLength']:
            return False, f"String length {len(value)} is less than minLength {constraints['minLength']}"

    if 'maxLength' in constraints and isinstance(value, str):
        if len(value) > constraints['maxLength']:
            return False, f"String length {len(value)} is greater than maxLength {constraints['maxLength']}"

    return True, ""


def validate_record(record: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a single record against a schema.

    Args:
        record: The data record (dictionary).
        schema: The JSON Schema definition.

    Returns:
        Tuple of (is_valid, list of error messages).
    """
    errors = []
    properties = schema.get('properties', {})
    required = schema.get('required', [])

    # Check required fields
    for field in required:
        if field not in record:
            errors.append(f"Missing required field: {field}")

    # Check field types and constraints
    for field, value in record.items():
        if field in properties:
            prop_schema = properties[field]
            expected_type = prop_schema.get('type')

            if expected_type and not validate_field_type(value, expected_type):
                errors.append(f"Field '{field}' has invalid type. Expected {expected_type}, got {type(value).__name__}")
            else:
                # Check constraints if type is valid
                is_valid, msg = validate_value_constraints(value, prop_schema)
                if not is_valid:
                    errors.append(f"Field '{field}': {msg}")

    return len(errors) == 0, errors


def validate_against_schema(data: Union[Dict, List], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate data using the jsonschema library.

    Args:
        data: The data to validate (dict or list of dicts).
        schema: The JSON Schema definition.

    Returns:
        Tuple of (is_valid, list of error messages).
    """
    if jsonschema is None:
        raise ImportError("jsonschema library is not installed. Please install it via requirements.txt.")

    errors = []
    try:
        if isinstance(data, list):
            for i, item in enumerate(data):
                try:
                    validate(instance=item, schema=schema)
                except JsonSchemaValidationError as e:
                    errors.append(f"Record {i}: {e.message}")
        else:
            try:
                validate(instance=data, schema=schema)
            except JsonSchemaValidationError as e:
                errors.append(f"Record: {e.message}")
    except Exception as e:
        errors.append(f"Validation error: {str(e)}")

    return len(errors) == 0, errors


def validate_dataset_file(file_path: str, schema: Optional[Dict[str, Any]] = None) -> bool:
    """
    Validate a CSV dataset file against the dataset schema.

    Args:
        file_path: Path to the CSV file.
        schema: Optional pre-loaded schema. If None, loads from DATASET_SCHEMA_PATH.

    Returns:
        True if valid, False otherwise.

    Raises:
        ValidationError: If the file is invalid or schema is missing.
    """
    if not os.path.exists(file_path):
        raise ValidationError(f"Dataset file not found: {file_path}")

    if schema is None:
        if not os.path.exists(DATASET_SCHEMA_PATH):
            raise ValidationError(f"Dataset schema not found at {DATASET_SCHEMA_PATH}. Ensure T007a is complete.")
        schema = load_schema(DATASET_SCHEMA_PATH)

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise ValidationError(f"Failed to read CSV file {file_path}: {e}")

    if df.empty:
        logger.warning(f"Dataset file {file_path} is empty. Validation skipped or failed depending on policy.")
        # Depending on strictness, empty might be valid or invalid. Here we assume non-empty is required for data.
        raise ValidationError(f"Dataset file {file_path} is empty.")

    # Convert to list of dicts for validation
    records = df.to_dict(orient='records')
    is_valid, errors = validate_against_schema(records, schema)

    if not is_valid:
        error_msg = "Validation failed for dataset:\n" + "\n".join(errors)
        logger.error(error_msg)
        raise ValidationError(error_msg)

    logger.info(f"Dataset file {file_path} validated successfully against {DATASET_SCHEMA_PATH}.")
    return True


def validate_output_file_structure(file_path: str, schema: Optional[Dict[str, Any]] = None) -> bool:
    """
    Validate an output CSV file against the output schema.

    Args:
        file_path: Path to the output CSV file.
        schema: Optional pre-loaded schema. If None, loads from OUTPUT_SCHEMA_PATH.

    Returns:
        True if valid, False otherwise.

    Raises:
        ValidationError: If the file is invalid or schema is missing.
    """
    if not os.path.exists(file_path):
        raise ValidationError(f"Output file not found: {file_path}")

    if schema is None:
        if not os.path.exists(OUTPUT_SCHEMA_PATH):
            raise ValidationError(f"Output schema not found at {OUTPUT_SCHEMA_PATH}. Ensure T007b is complete.")
        schema = load_schema(OUTPUT_SCHEMA_PATH)

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise ValidationError(f"Failed to read output CSV file {file_path}: {e}")

    if df.empty:
        # Output files might be allowed to be empty if no results, but usually we expect data.
        # For now, we validate structure even if empty, but warn.
        logger.warning(f"Output file {file_path} is empty.")

    records = df.to_dict(orient='records')
    is_valid, errors = validate_against_schema(records, schema)

    if not is_valid:
        error_msg = "Validation failed for output file:\n" + "\n".join(errors)
        logger.error(error_msg)
        raise ValidationError(error_msg)

    logger.info(f"Output file {file_path} validated successfully against {OUTPUT_SCHEMA_PATH}.")
    return True


def main():
    """
    Main entry point for command-line validation.
    Usage: python -m utils.validation [--dataset <path>] [--output <path>]
    """
    import argparse

    parser = argparse.ArgumentParser(description="Validate data and output files against schemas.")
    parser.add_argument('--dataset', type=str, help="Path to the dataset CSV file to validate.")
    parser.add_argument('--output', type=str, help="Path to the output CSV file to validate.")
    args = parser.parse_args()

    if not args.dataset and not args.output:
        print("Error: Must specify either --dataset or --output.")
        sys.exit(1)

    # Pre-check: Verify schemas exist
    if not os.path.exists(DATASET_SCHEMA_PATH):
        print(f"Error: Dataset schema missing at {DATASET_SCHEMA_PATH}. T007a may be incomplete.")
        sys.exit(1)
    if not os.path.exists(OUTPUT_SCHEMA_PATH):
        print(f"Error: Output schema missing at {OUTPUT_SCHEMA_PATH}. T007b may be incomplete.")
        sys.exit(1)

    if jsonschema is None:
        print("Error: jsonschema library is not installed. Please run 'pip install jsonschema'.")
        sys.exit(1)

    try:
        if args.dataset:
            validate_dataset_file(args.dataset)
            print(f"SUCCESS: {args.dataset} is valid.")

        if args.output:
            validate_output_file_structure(args.output)
            print(f"SUCCESS: {args.output} is valid.")

    except ValidationError as e:
        print(f"VALIDATION FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()