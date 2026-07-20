"""
Utility functions for contract validation, schema loading, and file I/O.

This module provides helpers for:
- Loading JSON/CSV schemas from disk
- Validating data structures against JSON schemas
- Safe JSON/CSV file loading and saving
- UUID validation
"""
import json
import csv
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from config import get_path


def load_schema(schema_name: str) -> Dict[str, Any]:
    """
    Load a JSON schema from the project's contracts directory.

    Args:
        schema_name: Name of the schema file (e.g., 'drift_result.schema.json')

    Returns:
        The loaded schema as a dictionary.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        json.JSONDecodeError: If the schema file is not valid JSON.
    """
    schema_path = get_path("contracts", schema_name)
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_against_schema(data: Union[Dict, List], schema: Dict[str, Any]) -> bool:
    """
    Validate data against a JSON schema.

    Note: This uses a simple manual validation approach to avoid adding
    a heavy dependency like `jsonschema` if not strictly necessary,
    but can be extended to use `jsonschema.validate` if the library is installed.

    Args:
        data: The data to validate (dict or list).
        schema: The schema dictionary.

    Returns:
        True if valid.

    Raises:
        ValueError: If validation fails.
    """
    # Simple type check
    expected_type = schema.get("type")
    if expected_type == "object" and not isinstance(data, dict):
        raise ValueError(f"Expected object, got {type(data).__name__}")
    elif expected_type == "array" and not isinstance(data, list):
        raise ValueError(f"Expected array, got {type(data).__name__}")

    # Check required fields
    if expected_type == "object":
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Check property types if defined
        properties = schema.get("properties", {})
        for key, value in data.items():
            if key in properties:
                prop_schema = properties[key]
                prop_type = prop_schema.get("type")
                if prop_type == "string" and not isinstance(value, str):
                    raise ValueError(f"Field '{key}' must be string, got {type(value).__name__}")
                elif prop_type == "number" and not isinstance(value, (int, float)):
                    raise ValueError(f"Field '{key}' must be number, got {type(value).__name__}")
                elif prop_type == "boolean" and not isinstance(value, bool):
                    raise ValueError(f"Field '{key}' must be boolean, got {type(value).__name__}")
                elif prop_type == "integer" and not isinstance(value, int):
                    raise ValueError(f"Field '{key}' must be integer, got {type(value).__name__}")

    return True


def load_json_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a JSON file and return its contents as a dictionary.

    Args:
        file_path: Path to the JSON file.

    Returns:
        Parsed JSON data.

    Raises:
        FileNotFoundError: If file does not exist.
        json.JSONDecodeError: If file is not valid JSON.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")

    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(data: Dict[str, Any], file_path: Union[str, Path]) -> None:
    """
    Save a dictionary to a JSON file.

    Args:
        data: Data to save.
        file_path: Destination path.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_csv_file(file_path: Union[str, Path]) -> List[Dict[str, str]]:
    """
    Load a CSV file and return a list of dictionaries.

    Args:
        file_path: Path to the CSV file.

    Returns:
        List of row dictionaries.

    Raises:
        FileNotFoundError: If file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    rows = []
    with open(path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows


def save_csv_file(data: List[Dict[str, Any]], file_path: Union[str, Path], fieldnames: Optional[List[str]] = None) -> None:
    """
    Save a list of dictionaries to a CSV file.

    Args:
        data: List of row dictionaries.
        file_path: Destination path.
        fieldnames: Optional list of column names. If None, keys from the first dict are used.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not data:
        # Create empty file if no data
        with open(path, 'w', encoding='utf-8', newline='') as f:
            pass
        return

    if fieldnames is None:
        fieldnames = list(data[0].keys())

    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def validate_drift_result_schema(result: Dict[str, Any]) -> bool:
    """
    Validate a drift result dictionary against the expected schema.

    Expected fields:
        - log_id: string (UUID format)
        - drift_score: number (float)
        - review_flag: boolean

    Args:
        result: The drift result dictionary.

    Returns:
        True if valid.

    Raises:
        ValueError: If validation fails.
    """
    required_fields = ['log_id', 'drift_score', 'review_flag']
    for field in required_fields:
        if field not in result:
            raise ValueError(f"Missing required field: {field}")

    # Validate log_id format (UUID4)
    if not is_valid_uuid4(result['log_id']):
        raise ValueError(f"Invalid UUID format for log_id: {result['log_id']}")

    # Validate drift_score type
    if not isinstance(result['drift_score'], (int, float)):
        raise ValueError(f"drift_score must be a number, got {type(result['drift_score']).__name__}")

    # Validate review_flag type
    if not isinstance(result['review_flag'], bool):
        raise ValueError(f"review_flag must be boolean, got {type(result['review_flag']).__name__}")

    return True


def is_valid_uuid4(uuid_string: str) -> bool:
    """
    Check if a string is a valid UUID4.

    Args:
        uuid_string: The string to validate.

    Returns:
        True if valid UUID4, False otherwise.
    """
    if not isinstance(uuid_string, str):
        return False

    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return bool(uuid_pattern.match(uuid_string))