"""
Utility functions for contract validation, schema loading, and data format helpers.

This module provides:
- JSON/CSV schema loading and validation helpers.
- Contract validation against YAML/JSON schema definitions.
- Common data transformation utilities used across the pipeline.
"""

import json
import csv
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

import yaml
from jsonschema import validate, ValidationError, Draft7Validator

from config import get_path


def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load a JSON or YAML schema from the given path.

    Args:
        schema_path: Relative or absolute path to the schema file.

    Returns:
        The loaded schema as a dictionary.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        ValueError: If the file format is unsupported.
    """
    full_path = get_path(schema_path)
    
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Schema file not found: {full_path}")

    with open(full_path, 'r', encoding='utf-8') as f:
        if schema_path.endswith('.yaml') or schema_path.endswith('.yml'):
            return yaml.safe_load(f)
        elif schema_path.endswith('.json'):
            return json.load(f)
        else:
            raise ValueError(f"Unsupported schema format: {schema_path}. Use .json or .yaml")


def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate data against a JSON schema.

    Args:
        data: The data to validate.
        schema: The JSON schema to validate against.

    Returns:
        True if valid.

    Raises:
        ValidationError: If the data does not match the schema.
    """
    try:
        validate(instance=data, schema=schema)
        return True
    except ValidationError as e:
        # Re-raise with more context if needed, or just re-raise
        raise e


def load_json_file(file_path: str) -> Dict[str, Any]:
    """
    Load a JSON file and return its contents as a dictionary.

    Args:
        file_path: Path to the JSON file.

    Returns:
        Parsed JSON data.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    full_path = get_path(file_path)
    with open(full_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_csv_file(file_path: str) -> List[Dict[str, str]]:
    """
    Load a CSV file and return its contents as a list of dictionaries.

    Args:
        file_path: Path to the CSV file.

    Returns:
        List of dictionaries where keys are column headers.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    full_path = get_path(file_path)
    with open(full_path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        return list(reader)


def save_json_file(data: Dict[str, Any], file_path: str, indent: int = 2) -> None:
    """
    Save a dictionary to a JSON file.

    Args:
        data: The data to save.
        file_path: Path where the JSON file will be saved.
        indent: Indentation level for pretty printing.
    """
    full_path = get_path(file_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def save_csv_file(data: List[Dict[str, Any]], file_path: str) -> None:
    """
    Save a list of dictionaries to a CSV file.

    Args:
        data: List of dictionaries to save.
        file_path: Path where the CSV file will be saved.
    """
    if not data:
        # Handle empty data case
        full_path = get_path(file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8', newline='') as f:
            f.write("")
        return

    full_path = get_path(file_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    # Determine headers from the first item
    fieldnames = list(data[0].keys())
    
    with open(full_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def validate_drift_result_schema(result: Dict[str, Any]) -> bool:
    """
    Validate a drift result object against the standard drift_result schema.
    
    This is a convenience wrapper for the specific schema used in US1.
    
    Args:
        result: The drift result dictionary to validate.
        
    Returns:
        True if valid.
        
    Raises:
        ValidationError: If the result does not match the schema.
    """
    # Load the schema from the contracts directory
    try:
        schema = load_schema("contracts/drift_result.schema.yaml")
    except FileNotFoundError:
        # If schema file is missing, we cannot validate, but we shouldn't crash the whole pipeline
        # depending on strictness. Here we assume schema must exist for validation.
        raise FileNotFoundError("drift_result.schema.yaml not found in contracts/")
    
    return validate_against_schema(result, schema)


def is_valid_uuid4(uuid_str: str) -> bool:
    """
    Basic check for UUID4 format string.
    
    Args:
        uuid_str: String to check.
        
    Returns:
        True if it looks like a valid UUID4 (length and hex chars).
    """
    if not isinstance(uuid_str, str):
        return False
    if len(uuid_str) != 36:
        return False
    try:
        parts = uuid_str.split('-')
        if len(parts) != 5:
            return False
        # Check lengths: 8-4-4-4-12
        if [len(p) for p in parts] != [8, 4, 4, 4, 12]:
            return False
        # Check hex
        int(uuid_str.replace('-', ''), 16)
        return True
    except ValueError:
        return False