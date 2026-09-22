"""
Schema Validator Module for BIDS events.tsv files.

This module provides utilities to load a JSON/YAML schema and validate
BIDS events.tsv files against it. It enforces strict validation rules
and exits with specific error codes for different failure modes.
"""

import os
import sys
import json
import csv
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

try:
    import jsonschema
    from jsonschema import validate, ValidationError, SchemaError
except ImportError:
    # Fallback if jsonschema is not installed, though it should be per requirements.txt
    print("ERROR: jsonschema library is required. Install with: pip install jsonschema")
    sys.exit(1)


class SchemaValidationError(Exception):
    """Custom exception for schema validation failures."""
    pass


class FileLoadError(Exception):
    """Custom exception for file loading failures."""
    pass


def load_schema_from_file(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a JSON or YAML schema from the given file path.

    Args:
        schema_path: Path to the schema file (.json, .yaml, .yml).

    Returns:
        The loaded schema as a dictionary.

    Raises:
        FileLoadError: If the file cannot be read or parsed.
    """
    schema_path = Path(schema_path)
    if not schema_path.exists():
        raise FileLoadError(f"Schema file not found: {schema_path}")

    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            if schema_path.suffix in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            elif schema_path.suffix == '.json':
                return json.load(f)
            else:
                raise FileLoadError(f"Unsupported schema file format: {schema_path.suffix}")
    except yaml.YAMLError as e:
        raise FileLoadError(f"Failed to parse YAML schema: {e}")
    except json.JSONDecodeError as e:
        raise FileLoadError(f"Failed to parse JSON schema: {e}")
    except Exception as e:
        raise FileLoadError(f"Unexpected error loading schema: {e}")


def validate_data_against_schema(data: List[Dict[str, Any]], schema: Dict[str, Any]) -> bool:
    """
    Validate a list of row dictionaries against a JSON Schema.

    Note: JSON Schema validates a single object. To validate a TSV (list of objects),
    we validate each row individually or wrap them if the schema expects an array.
    Given the typical BIDS events.tsv structure, we validate each row against the
    properties defined in the schema.

    Args:
        data: List of dictionaries representing rows in the TSV.
        schema: The JSON Schema dictionary.

    Returns:
        True if all rows are valid.

    Raises:
        SchemaValidationError: If validation fails.
    """
    # Adjust schema to validate a single row (the schema usually defines properties of a record)
    # We assume the provided schema defines the structure of a single event row.
    row_schema = schema

    for i, row in enumerate(data):
        try:
            validate(instance=row, schema=row_schema)
        except ValidationError as e:
            raise SchemaValidationError(f"Row {i} validation failed: {e.message}")
        except SchemaError as e:
            raise SchemaValidationError(f"Schema error during validation of row {i}: {e.message}")

    return True


def validate_file_against_schema(file_path: Union[str, Path], schema_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a TSV file and validate its contents against a schema.

    Args:
        file_path: Path to the events.tsv file.
        schema_path: Path to the schema file.

    Returns:
        A dictionary with 'valid': bool and 'errors': list of error messages.

    Raises:
        FileLoadError: If files cannot be loaded.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileLoadError(f"Data file not found: {file_path}")

    schema = load_schema_from_file(schema_path)

    # Load TSV
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            rows = list(reader)
    except Exception as e:
        raise FileLoadError(f"Failed to read TSV file: {e}")

    if not rows:
        # Empty file is technically valid if schema allows empty, but usually implies missing data
        # We'll consider it valid but warn in the result if needed.
        return {'valid': True, 'errors': [], 'rows_validated': 0}

    errors = []
    try:
        validate_data_against_schema(rows, schema)
    except SchemaValidationError as e:
        errors.append(str(e))
    except Exception as e:
        errors.append(f"Unexpected validation error: {e}")

    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'rows_validated': len(rows)
    }


def validate_contract_input(data_path: Union[str, Path], schema_path: Union[str, Path]) -> int:
    """
    Validate a BIDS events.tsv file against a schema and exit with appropriate code.

    Exit Codes:
        0: Validation successful.
        1: File not found (Data or Schema).
        2: Schema parsing error.
        3: Data parsing error (TSV read failure).
        4: Validation failed (Schema mismatch).

    Args:
        data_path: Path to the events.tsv file.
        schema_path: Path to the schema file.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    data_path = Path(data_path)
    schema_path = Path(schema_path)

    # Check Schema existence first
    if not schema_path.exists():
        print(f"ERROR: Schema file not found: {schema_path}", file=sys.stderr)
        return 2

    # Check Data existence
    if not data_path.exists():
        print(f"ERROR: Data file not found: {data_path}", file=sys.stderr)
        return 1

    try:
        schema = load_schema_from_file(schema_path)
    except FileLoadError as e:
        print(f"ERROR: Schema loading failed: {e}", file=sys.stderr)
        return 2

    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            rows = list(reader)
    except Exception as e:
        print(f"ERROR: Data file parsing failed: {e}", file=sys.stderr)
        return 3

    if not rows:
        print(f"WARNING: Data file {data_path} is empty.", file=sys.stderr)
        # Empty file is not necessarily a validation failure against the schema,
        # but depends on strictness. For now, we treat it as valid but warn.
        return 0

    try:
        validate_data_against_schema(rows, schema)
        print(f"SUCCESS: {data_path} is valid against {schema_path}.")
        return 0
    except SchemaValidationError as e:
        print(f"ERROR: Validation failed for {data_path}: {e}", file=sys.stderr)
        return 4
    except Exception as e:
        print(f"ERROR: Unexpected error during validation: {e}", file=sys.stderr)
        return 5


def main():
    """
    Command-line entry point for schema validation.
    Expects two arguments: <data_file> <schema_file>
    """
    if len(sys.argv) != 3:
        print("Usage: python -m utils.schema_validator <data_file.tsv> <schema_file.yaml/json>", file=sys.stderr)
        sys.exit(64) # EX_USAGE

    data_path = sys.argv[1]
    schema_path = sys.argv[2]

    exit_code = validate_contract_input(data_path, schema_path)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()