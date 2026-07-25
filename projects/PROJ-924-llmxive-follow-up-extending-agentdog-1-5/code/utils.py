"""
Utility functions for contract validation, JSON/CSV schema loading, and data file handling.
"""
import json
import csv
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from config import get_path


class SchemaValidationError(Exception):
    """Raised when data validation against a schema fails."""
    pass


def load_json_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load and parse a JSON file.

    Args:
        file_path: Path to the JSON file.

    Returns:
        Parsed JSON content as a dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
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
        data: Dictionary to save.
        file_path: Path to the output JSON file.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_csv_file(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Load a CSV file and return a list of dictionaries (one per row).

    Args:
        file_path: Path to the CSV file.

    Returns:
        List of dictionaries where keys are column names.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    with open(path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        return list(reader)


def save_csv_file(data: List[Dict[str, Any]], file_path: Union[str, Path], fieldnames: Optional[List[str]] = None) -> None:
    """
    Save a list of dictionaries to a CSV file.

    Args:
        data: List of dictionaries to save.
        file_path: Path to the output CSV file.
        fieldnames: Optional list of column names. If None, keys from the first dict are used.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not data:
        # Create empty file with no rows if data is empty
        with open(path, 'w', encoding='utf-8', newline='') as f:
            pass
        return

    if fieldnames is None:
        fieldnames = list(data[0].keys())

    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def load_schema(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a JSON schema definition.

    Args:
        schema_path: Path to the schema JSON file.

    Returns:
        Parsed schema dictionary.
    """
    return load_json_file(schema_path)


def validate_against_schema(data: Union[Dict[str, Any], List[Dict[str, Any]]], schema: Dict[str, Any]) -> bool:
    """
    Validate data against a JSON schema.
    This is a simplified validator that checks required fields and basic types.
    For full JSON Schema validation, the 'jsonschema' library would be used.

    Args:
        data: Data to validate (dict or list of dicts).
        schema: The schema dictionary.

    Returns:
        True if validation passes.

    Raises:
        SchemaValidationError: If validation fails.
    """
    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})

    def check_dict(d: Dict[str, Any], schema_props: Dict[str, Any], req_fields: List[str], context: str) -> None:
        # Check required fields
        for field in req_fields:
            if field not in d:
                raise SchemaValidationError(f"Missing required field '{field}' in {context}")

        # Check types for existing fields
        for field, value in d.items():
            if field in schema_props:
                expected_type = schema_props[field].get('type')
                if expected_type == 'string' and not isinstance(value, str):
                    raise SchemaValidationError(f"Field '{field}' in {context} must be a string, got {type(value).__name__}")
                elif expected_type == 'number' and not isinstance(value, (int, float)):
                    raise SchemaValidationError(f"Field '{field}' in {context} must be a number, got {type(value).__name__}")
                elif expected_type == 'boolean' and not isinstance(value, bool):
                    raise SchemaValidationError(f"Field '{field}' in {context} must be a boolean, got {type(value).__name__}")
                elif expected_type == 'array' and not isinstance(value, list):
                    raise SchemaValidationError(f"Field '{field}' in {context} must be an array, got {type(value).__name__}")

    if isinstance(data, list):
        for idx, item in enumerate(data):
            if not isinstance(item, dict):
                raise SchemaValidationError(f"Item at index {idx} is not an object")
            check_dict(item, properties, required_fields, f"list item {idx}")
    elif isinstance(data, dict):
        check_dict(data, properties, required_fields, "root object")
    else:
        raise SchemaValidationError(f"Data must be a dict or list of dicts, got {type(data).__name__}")

    return True


def is_valid_uuid4(uuid_str: str) -> bool:
    """
    Validate if a string is a valid UUID4.

    Args:
        uuid_str: String to validate.

    Returns:
        True if valid UUID4, False otherwise.
    """
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
    return bool(re.match(pattern, uuid_str.lower()))


def load_config_schema() -> Dict[str, Any]:
    """
    Load the configuration schema.

    Returns:
        Configuration schema dictionary.
    """
    schema_path = get_path('specs/001-llmxive-drift-detection/contracts/config.schema.yaml')
    # Convert .yaml to .json if needed, or load as JSON if stored as JSON
    if not os.path.exists(schema_path):
        # Fallback to common location if yaml not found
        schema_path = schema_path.replace('.yaml', '.json')
    return load_json_file(schema_path)


def load_drift_result_schema() -> Dict[str, Any]:
    """
    Load the drift result schema.

    Returns:
        Drift result schema dictionary.
    """
    schema_path = get_path('specs/001-llmxive-drift-detection/contracts/drift_result.schema.yaml')
    if not os.path.exists(schema_path):
        schema_path = schema_path.replace('.yaml', '.json')
    return load_json_file(schema_path)


def validate_drift_result_schema(data: List[Dict[str, Any]]) -> bool:
    """
    Validate drift result data against the schema.

    Args:
        data: List of drift result dictionaries.

    Returns:
        True if valid.

    Raises:
        SchemaValidationError: If validation fails.
    """
    schema = load_drift_result_schema()
    return validate_against_schema(data, schema)

def load_taxonomy_mapping_file() -> Dict[str, Any]:
    """
    Load the taxonomy mapping file.

    Returns:
        Taxonomy mapping dictionary.
    """
    return load_json_file(get_path('data/raw/taxonomy_agentdog.json'))

def save_taxonomy_mapping_file(data: Dict[str, Any]) -> None:
    """
    Save the taxonomy mapping file.

    Args:
        data: Taxonomy mapping dictionary.
    """
    save_json_file(data, get_path('data/raw/taxonomy_agentdog.json'))

def load_centroids_file() -> Dict[str, Any]:
    """
    Load the centroids file.

    Returns:
        Centroids dictionary.
    """
    return load_json_file(get_path('data/processed/taxonomy_centroids.json'))

def save_centroids_file(data: Dict[str, Any]) -> None:
    """
    Save the centroids file.

    Args:
        data: Centroids dictionary.
    """
    save_json_file(data, get_path('data/processed/taxonomy_centroids.json'))

def load_drift_scores_file() -> List[Dict[str, Any]]:
    """
    Load the drift scores CSV file.

    Returns:
        List of drift score dictionaries.
    """
    return load_csv_file(get_path('data/processed/drift_scores.csv'))

def save_drift_scores_file(data: List[Dict[str, Any]]) -> None:
    """
    Save the drift scores CSV file.

    Args:
        data: List of drift score dictionaries.
    """
    save_csv_file(data, get_path('data/processed/drift_scores.csv'))

def load_ground_truth_fixture() -> List[Dict[str, Any]]:
    """
    Load the ground truth fixture file.

    Returns:
        List of ground truth dictionaries.
    """
    return load_json_file(get_path('data/test/real_ground_truth_fixture.json'))

def save_ground_truth_fixture(data: List[Dict[str, Any]]) -> None:
    """
    Save the ground truth fixture file.

    Args:
        data: List of ground truth dictionaries.
    """
    save_json_file(data, get_path('data/test/real_ground_truth_fixture.json'))