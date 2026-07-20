"""
utils.py - Contract validation helpers and JSON/CSV schema loading.

This module provides utilities for:
- Loading JSON and CSV files with error handling.
- Loading JSON schemas from disk.
- Validating data against JSON schemas.
- Saving data to JSON and CSV formats.
- Specific validation helpers for drift result contracts.
"""
import json
import csv
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

# Import config for path resolution if needed, though this module is standalone
# from config import get_path

def load_json_file(path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a JSON file from disk.

    Args:
        path: Path to the JSON file.

    Returns:
        Parsed JSON content as a dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file content is not valid JSON.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(data: Dict[str, Any], path: Union[str, Path], indent: int = 2) -> None:
    """
    Save a dictionary to a JSON file.

    Args:
        data: Dictionary to save.
        path: Path to the output JSON file.
        indent: Indentation level for formatting.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent)

def load_csv_file(path: Union[str, Path]) -> List[Dict[str, str]]:
    """
    Load a CSV file from disk into a list of dictionaries.

    Args:
        path: Path to the CSV file.

    Returns:
        List of dictionaries, where each dictionary represents a row.

    Raises:
        FileNotFoundError: If the file does not exist.
        csv.Error: If the CSV is malformed.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def save_csv_file(data: List[Dict[str, Any]], path: Union[str, Path], fieldnames: Optional[List[str]] = None) -> None:
    """
    Save a list of dictionaries to a CSV file.

    Args:
        data: List of dictionaries to save.
        path: Path to the output CSV file.
        fieldnames: Optional list of fieldnames. If None, derived from the first dict.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if not data:
        # Create empty file if no data
        with open(path, 'w', encoding='utf-8') as f:
            pass
        return

    if fieldnames is None:
        fieldnames = list(data[0].keys())

    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def load_schema(path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a JSON schema from disk.

    Args:
        path: Path to the schema file.

    Returns:
        Parsed schema as a dictionary.
    """
    return load_json_file(path)

def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate data against a JSON schema.
    
    Note: This is a lightweight implementation. For complex schemas, 
    the 'jsonschema' library is recommended, but this function provides
    basic type and required field checking.

    Args:
        data: Data to validate.
        schema: The JSON schema.

    Returns:
        True if valid.

    Raises:
        ValueError: If validation fails.
    """
    # Basic required fields check
    required = schema.get('required', [])
    for field in required:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    
    # Basic type checking if schema defines types
    properties = schema.get('properties', {})
    for key, value in data.items():
        if key in properties:
            prop_schema = properties[key]
            expected_type = prop_schema.get('type')
            if expected_type:
                if expected_type == 'string' and not isinstance(value, str):
                    raise ValueError(f"Field '{key}' must be a string")
                if expected_type == 'number' and not isinstance(value, (int, float)):
                    raise ValueError(f"Field '{key}' must be a number")
                if expected_type == 'integer' and not isinstance(value, int):
                    raise ValueError(f"Field '{key}' must be an integer")
                if expected_type == 'boolean' and not isinstance(value, bool):
                    raise ValueError(f"Field '{key}' must be a boolean")
                if expected_type == 'array' and not isinstance(value, list):
                    raise ValueError(f"Field '{key}' must be an array")
                if expected_type == 'object' and not isinstance(value, dict):
                    raise ValueError(f"Field '{key}' must be an object")
    
    return True

def is_valid_uuid4(uuid_string: str) -> bool:
    """
    Check if a string is a valid UUID4.

    Args:
        uuid_string: The string to check.

    Returns:
        True if valid UUID4 format.
    """
    pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return bool(pattern.match(uuid_string))

def validate_drift_result_schema(data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> bool:
    """
    Validate a drift result record or list of records against the expected contract.
    
    Expected fields per record:
      - log_id (string, UUID4 recommended)
      - drift_score (number)
      - review_flag (boolean)
      - category (optional string)

    Args:
        data: A single record or a list of records.

    Returns:
        True if valid.

    Raises:
        ValueError: If validation fails.
    """
    records = data if isinstance(data, list) else [data]
    
    for i, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"Record {i} is not a dictionary")
        
        # Required fields
        if 'log_id' not in record:
            raise ValueError(f"Record {i} missing 'log_id'")
        if not isinstance(record['log_id'], str):
            raise ValueError(f"Record {i} 'log_id' must be a string")
        
        if 'drift_score' not in record:
            raise ValueError(f"Record {i} missing 'drift_score'")
        if not isinstance(record['drift_score'], (int, float)):
            raise ValueError(f"Record {i} 'drift_score' must be a number")
        
        if 'review_flag' not in record:
            raise ValueError(f"Record {i} missing 'review_flag'")
        if not isinstance(record['review_flag'], bool):
            raise ValueError(f"Record {i} 'review_flag' must be a boolean")
        
        # Optional validation for log_id format if it looks like a UUID
        if is_valid_uuid4(record['log_id']):
            pass # Valid UUID4
        # We don't strictly enforce UUID4 if it's just a string ID, but we accept it.

    return True