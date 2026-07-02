"""
Schema validation utilities for CMB-LSS statistical outputs.

This module provides functions to validate JSON output files against the
defined schema (contracts/cmb_lss_schema.schema.yaml) to ensure data
integrity and compliance with project specifications.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import yaml
from jsonschema import validate, ValidationError, Draft7Validator

logger = logging.getLogger(__name__)


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """
    Load a JSON Schema from a YAML file.

    Args:
        schema_path: Path to the schema file (YAML format)

    Returns:
        Dictionary containing the parsed schema

    Raises:
        FileNotFoundError: If schema file does not exist
        yaml.YAMLError: If schema file is not valid YAML
    """
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)

    return schema


def validate_output(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate data against a JSON Schema.

    Args:
        data: The data dictionary to validate
        schema: The JSON Schema to validate against

    Returns:
        Tuple of (is_valid, error_message)
        If valid, error_message is None
        If invalid, error_message contains the validation error
    """
    validator = Draft7Validator(schema)
    errors = list(validator.iter_errors(data))

    if not errors:
        return True, None

    # Return the first error message
    error = errors[0]
    path = " -> ".join(str(p) for p in error.path) if error.path else "root"
    error_msg = f"Validation failed at {path}: {error.message}"
    return False, error_msg


def validate_json_file(output_path: Path, schema_path: Optional[Path] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate a JSON file against the CMB-LSS schema.

    Args:
        output_path: Path to the JSON file to validate
        schema_path: Optional path to schema file (defaults to contracts/cmb_lss_schema.schema.yaml)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if schema_path is None:
        schema_path = Path("contracts/cmb_lss_schema.schema.yaml")

    try:
        schema = load_schema(schema_path)
    except (FileNotFoundError, yaml.YAMLError) as e:
        return False, f"Failed to load schema: {e}"

    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON in output file: {e}"
    except FileNotFoundError:
        return False, f"Output file not found: {output_path}"

    return validate_output(data, schema)


def validate_and_log(output_path: Path, schema_path: Optional[Path] = None) -> bool:
    """
    Validate a JSON file and log the result.

    Args:
        output_path: Path to the JSON file to validate
        schema_path: Optional path to schema file

    Returns:
        True if valid, False otherwise
    """
    is_valid, error_msg = validate_json_file(output_path, schema_path)

    if is_valid:
        logger.info(f"Validation passed for {output_path}")
    else:
        logger.error(f"Validation failed for {output_path}: {error_msg}")

    return is_valid


def main():
    """
    CLI entry point for schema validation.
    Usage: python -m utils.schema_validator <output_file.json> [schema_file.yaml]
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m utils.schema_validator <output_file.json> [schema_file.yaml]")
        sys.exit(1)

    output_path = Path(sys.argv[1])
    schema_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    is_valid, error_msg = validate_json_file(output_path, schema_path)

    if is_valid:
        print(f"✓ Validation passed: {output_path}")
        sys.exit(0)
    else:
        print(f"✗ Validation failed: {output_path}")
        print(f"  Error: {error_msg}")
        sys.exit(1)


if __name__ == "__main__":
    main()
