"""
Schema Validator Module for BIDS events.tsv validation.

This module provides functionality to load a JSON Schema from a YAML file
and validate BIDS events.tsv files against it. It implements strict error
handling with specific exit codes for different failure modes.
"""

import os
import sys
import json
import csv
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import re

class SchemaValidationError(Exception):
    """Raised when data validation against the schema fails."""
    pass

class FileLoadError(Exception):
    """Raised when a file (schema or data) cannot be loaded."""
    pass

class InvalidFormatError(Exception):
    """Raised when the file format is not supported (e.g., not TSV)."""
    pass

# Exit codes
EXIT_SUCCESS = 0
EXIT_SCHEMA_MISSING = 1
EXIT_FILE_MISSING = 2
EXIT_INVALID_FORMAT = 3
EXIT_SCHEMA_MISMATCH = 4
EXIT_LOAD_ERROR = 5

def load_schema_from_file(schema_path: str) -> Dict[str, Any]:
    """
    Load a JSON Schema from a YAML file.

    Args:
        schema_path: Path to the schema YAML file.

    Returns:
        The schema as a dictionary.

    Raises:
        FileLoadError: If the schema file cannot be read or parsed.
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileLoadError(f"Schema file not found: {schema_path}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
            if not isinstance(schema, dict):
                raise FileLoadError("Schema file must contain a YAML dictionary/object")
            return schema
    except yaml.YAMLError as e:
        raise FileLoadError(f"Failed to parse YAML schema: {e}")
    except IOError as e:
        raise FileLoadError(f"Failed to read schema file: {e}")

def _validate_required_columns(data: List[Dict[str, Any]], schema: Dict[str, Any]) -> List[str]:
    """
    Check that all required columns from the schema are present in the data.

    Args:
        data: List of rows (dictionaries) from the TSV.
        schema: The JSON Schema definition.

    Returns:
        List of missing required column names.
    """
    required_columns = []
    properties = schema.get('properties', {})

    # Extract required fields from schema
    schema_required = schema.get('required', [])

    # Check each required field exists in the first row (headers)
    if data:
        headers = set(data[0].keys())
        for field in schema_required:
            if field not in headers:
                required_columns.append(field)

    return required_columns

def _validate_column_types(data: List[Dict[str, Any]], schema: Dict[str, Any]) -> List[str]:
    """
    Validate that column values match the types defined in the schema.

    Args:
        data: List of rows from the TSV.
        schema: The JSON Schema definition.

    Returns:
        List of validation error messages.
    """
    errors = []
    properties = schema.get('properties', {})

    for row_idx, row in enumerate(data):
        for col_name, col_schema in properties.items():
            if col_name not in row:
                continue

            value = row[col_name]
            expected_type = col_schema.get('type')
            enum_values = col_schema.get('enum')

            # Handle numeric types (int/float) - TSV reads everything as string
            if expected_type in ['integer', 'number']:
                try:
                    float(value)
                except (ValueError, TypeError):
                    errors.append(f"Row {row_idx}: Column '{col_name}' expected {expected_type}, got '{value}'")

            # Handle string type with enum constraint
            if expected_type == 'string' and enum_values:
                if value not in enum_values:
                    errors.append(f"Row {row_idx}: Column '{col_name}' value '{value}' not in allowed values: {enum_values}")

            # Handle string type (basic check)
            if expected_type == 'string' and not isinstance(value, str):
                errors.append(f"Row {row_idx}: Column '{col_name}' expected string, got {type(value).__name__}")

    return errors

def validate_data_against_schema(data: List[Dict[str, Any]], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a list of data rows against a schema.

    Args:
        data: List of dictionaries representing rows.
        schema: The JSON Schema to validate against.

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []

    # Check required columns
    missing_cols = _validate_required_columns(data, schema)
    if missing_cols:
        errors.append(f"Missing required columns: {', '.join(missing_cols)}")

    # Check type constraints
    type_errors = _validate_column_types(data, schema)
    errors.extend(type_errors)

    return len(errors) == 0, errors

def validate_file_against_schema(file_path: str, schema_path: str) -> Tuple[bool, List[str]]:
    """
    Validate a TSV file against a schema file.

    Args:
        file_path: Path to the TSV file to validate.
        schema_path: Path to the schema YAML file.

    Returns:
        Tuple of (is_valid, list_of_errors).

    Raises:
        FileLoadError: If files cannot be loaded.
        InvalidFormatError: If the file is not a valid TSV.
    """
    # Load schema
    try:
        schema = load_schema_from_file(schema_path)
    except FileLoadError as e:
        raise e

    # Check if data file exists
    data_path = Path(file_path)
    if not data_path.exists():
        raise FileLoadError(f"Data file not found: {file_path}")

    # Load and parse TSV
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            data = list(reader)
    except csv.Error as e:
        raise InvalidFormatError(f"Invalid TSV format: {e}")
    except IOError as e:
        raise FileLoadError(f"Failed to read data file: {e}")

    # Validate
    is_valid, errors = validate_data_against_schema(data, schema)
    return is_valid, errors

def validate_contract_input(input_path: str, schema_path: str) -> int:
    """
    Validate a file against a schema and return an exit code.

    This function implements the error contract for the pipeline:
    - 0: Success
    - 1: Schema missing
    - 2: File missing
    - 3: Invalid format
    - 4: Schema mismatch
    - 5: Load error

    Args:
        input_path: Path to the TSV file to validate.
        schema_path: Path to the schema YAML file.

    Returns:
        Exit code indicating result.
    """
    # Check schema exists
    if not Path(schema_path).exists():
        print(f"ERROR: Schema file not found: {schema_path}", file=sys.stderr)
        return EXIT_SCHEMA_MISSING

    # Check data file exists
    if not Path(input_path).exists():
        print(f"ERROR: Data file not found: {input_path}", file=sys.stderr)
        return EXIT_FILE_MISSING

    try:
        is_valid, errors = validate_file_against_schema(input_path, schema_path)
        if not is_valid:
            print("ERROR: Schema validation failed:", file=sys.stderr)
            for err in errors:
                print(f"  - {err}", file=sys.stderr)
            return EXIT_SCHEMA_MISMATCH
        return EXIT_SUCCESS

    except FileLoadError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return EXIT_LOAD_ERROR
    except InvalidFormatError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return EXIT_INVALID_FORMAT

def main():
    """
    Command-line entry point for schema validation.

    Usage:
        python -m code.utils.schema_validator <data_file> <schema_file>

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    if len(sys.argv) != 3:
        print("Usage: python -m code.utils.schema_validator <data_file> <schema_file>", file=sys.stderr)
        return EXIT_LOAD_ERROR

    data_file = sys.argv[1]
    schema_file = sys.argv[2]

    return validate_contract_input(data_file, schema_file)

if __name__ == '__main__':
    sys.exit(main())