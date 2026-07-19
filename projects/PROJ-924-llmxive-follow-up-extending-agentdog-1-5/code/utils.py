"""
utils.py - Contract validation helpers and JSON/CSV schema loading.

This module provides utility functions for:
- Loading and validating JSON schemas (YAML/JSON format)
- Loading and saving JSON/CSV files
- Validating data against schemas
- UUID validation
"""

import json
import csv
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

# Try to import yaml, but handle if not installed
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


def load_schema(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a JSON or YAML schema from the given path.

    Args:
        schema_path: Path to the schema file (.json or .yaml/.yml)

    Returns:
        Dictionary containing the parsed schema

    Raises:
        FileNotFoundError: If the schema file does not exist
        ValueError: If the file format is unsupported or parsing fails
    """
    schema_path = Path(schema_path)

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if schema_path.suffix in ['.yaml', '.yml']:
        if not YAML_AVAILABLE:
            raise ImportError(
                "PyYAML is required to load YAML schemas. "
                "Install it with: pip install pyyaml"
            )
        return yaml.safe_load(content)
    elif schema_path.suffix == '.json':
        return json.loads(content)
    else:
        raise ValueError(f"Unsupported schema format: {schema_path.suffix}. "
                       "Use .json or .yaml/.yml")


def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate data against a JSON schema and return a list of errors.

    This is a simplified validator that checks:
    - Required fields are present
    - Field types match the schema definition

    For full JSON Schema validation, use the 'jsonschema' library.

    Args:
        data: The data to validate
        schema: The JSON schema to validate against

    Returns:
        List of error messages. Empty list if validation passes.
    """
    errors = []

    # Check required fields
    required_fields = schema.get('required', [])
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    # Check property types
    properties = schema.get('properties', {})
    for field, definition in properties.items():
        if field in data:
            expected_type = definition.get('type')
            value = data[field]

            if expected_type == 'string':
                if not isinstance(value, str):
                    errors.append(f"Field '{field}' must be a string, got {type(value).__name__}")
            elif expected_type == 'number':
                if not isinstance(value, (int, float)):
                    errors.append(f"Field '{field}' must be a number, got {type(value).__name__}")
            elif expected_type == 'integer':
                if not isinstance(value, int):
                    errors.append(f"Field '{field}' must be an integer, got {type(value).__name__}")
            elif expected_type == 'boolean':
                if not isinstance(value, bool):
                    errors.append(f"Field '{field}' must be a boolean, got {type(value).__name__}")
            elif expected_type == 'array':
                if not isinstance(value, list):
                    errors.append(f"Field '{field}' must be an array, got {type(value).__name__}")
            elif expected_type == 'object':
                if not isinstance(value, dict):
                    errors.append(f"Field '{field}' must be an object, got {type(value).__name__}")

    return errors


def load_json_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a JSON file and return its contents as a dictionary.

    Args:
        file_path: Path to the JSON file

    Returns:
        Dictionary containing the parsed JSON data

    Raises:
        FileNotFoundError: If the file does not exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(data: Dict[str, Any], file_path: Union[str, Path], indent: int = 2) -> None:
    """
    Save a dictionary to a JSON file.

    Args:
        data: Dictionary to save
        file_path: Path to the output file
        indent: Indentation level for pretty-printing (default: 2)
    """
    file_path = Path(file_path)

    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def load_csv_file(file_path: Union[str, Path]) -> List[Dict[str, str]]:
    """
    Load a CSV file and return its contents as a list of dictionaries.

    Args:
        file_path: Path to the CSV file

    Returns:
        List of dictionaries, where each dictionary represents a row
        with column names as keys

    Raises:
        FileNotFoundError: If the file does not exist
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        return list(reader)


def save_csv_file(data: List[Dict[str, Any]], file_path: Union[str, Path]) -> None:
    """
    Save a list of dictionaries to a CSV file.

    Args:
        data: List of dictionaries to save (each dict is a row)
        file_path: Path to the output file
    """
    file_path = Path(file_path)

    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    if not data:
        # Write empty file if no data
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            pass
        return

    # Get fieldnames from the first row
    fieldnames = list(data[0].keys())

    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def validate_drift_result_schema(result: Dict[str, Any]) -> List[str]:
    """
    Validate a drift scoring result against the expected schema.

    Expected schema for drift result:
    {
        "log_id": "string (UUID)",
        "drift_score": "number (0.0 to 2.0)",
        "review_flag": "boolean or string ('true'/'false')"
    }

    Args:
        result: The drift result dictionary to validate

    Returns:
        List of error messages. Empty list if validation passes.
    """
    errors = []

    # Check required fields
    required_fields = ['log_id', 'drift_score', 'review_flag']
    for field in required_fields:
        if field not in result:
            errors.append(f"Missing required field: {field}")

    # Validate log_id format (UUID4)
    if 'log_id' in result:
        if not is_valid_uuid4(result['log_id']):
            errors.append(f"Invalid UUID4 format for log_id: {result['log_id']}")

    # Validate drift_score range
    if 'drift_score' in result:
        score = result['drift_score']
        if not isinstance(score, (int, float)):
            errors.append(f"drift_score must be a number, got {type(score).__name__}")
        elif not (0.0 <= score <= 2.0):
            errors.append(f"drift_score must be between 0.0 and 2.0, got {score}")

    # Validate review_flag
    if 'review_flag' in result:
        flag = result['review_flag']
        valid_flags = [True, False, 'true', 'false', 'True', 'False', 1, 0]
        if flag not in valid_flags:
            errors.append(f"Invalid review_flag value: {flag}. "
                        f"Expected boolean or 'true'/'false' string")

    return errors


def is_valid_uuid4(uuid_str: str) -> bool:
    """
    Check if a string is a valid UUID4.

    Args:
        uuid_str: String to validate

    Returns:
        True if the string is a valid UUID4, False otherwise
    """
    # UUID4 pattern: 8-4-4-4-12 hex digits
    pattern = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$'
    return bool(re.match(pattern, uuid_str))