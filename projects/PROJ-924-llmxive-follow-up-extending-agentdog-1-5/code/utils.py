"""
utils.py - Contract validation helpers and JSON/CSV schema loading.

This module provides utilities for:
- Loading and saving JSON/CSV files
- Loading JSON Schema definitions
- Validating data against schemas
- UUID validation
"""

import json
import csv
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

# Import config utilities for path resolution
from config import get_path, ensure_directories


class SchemaValidationError(Exception):
    """Raised when data validation against a schema fails."""
    pass


def load_json_file(path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a JSON file and return its contents as a dictionary.

    Args:
        path: Path to the JSON file.

    Returns:
        Dictionary containing the JSON data.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
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
        indent: Indentation level for pretty-printing.
    """
    path = Path(path)
    ensure_directories([path.parent])

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def load_csv_file(path: Union[str, Path]) -> List[Dict[str, str]]:
    """
    Load a CSV file and return its contents as a list of dictionaries.

    Args:
        path: Path to the CSV file.

    Returns:
        List of dictionaries where keys are column names.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    with open(path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        return list(reader)


def save_csv_file(data: List[Dict[str, Any]], path: Union[str, Path]) -> None:
    """
    Save a list of dictionaries to a CSV file.

    Args:
        data: List of dictionaries to save.
        path: Path to the output CSV file.
    """
    if not data:
        # Create empty file if no data
        path = Path(path)
        ensure_directories([path.parent])
        with open(path, 'w', encoding='utf-8', newline='') as f:
            pass
        return

    path = Path(path)
    ensure_directories([path.parent])

    fieldnames = list(data[0].keys())
    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def load_schema(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a JSON Schema definition from a file.

    Args:
        schema_path: Path to the schema file.

    Returns:
        Dictionary containing the schema definition.
    """
    return load_json_file(schema_path)


def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate data against a JSON Schema.

    This is a basic validator that checks required fields and types.
    For full validation, consider using the 'jsonschema' library.

    Args:
        data: Data to validate.
        schema: JSON Schema definition.

    Returns:
        True if valid.

    Raises:
        SchemaValidationError: If validation fails.
    """
    # Check required fields
    required = schema.get('required', [])
    for field in required:
        if field not in data:
            raise SchemaValidationError(f"Missing required field: {field}")

    # Check property types (basic implementation)
    properties = schema.get('properties', {})
    for field, value in data.items():
        if field in properties:
            expected_type = properties[field].get('type')
            if expected_type:
                if expected_type == 'string' and not isinstance(value, str):
                    raise SchemaValidationError(f"Field '{field}' must be a string")
                elif expected_type == 'integer' and not isinstance(value, int):
                    raise SchemaValidationError(f"Field '{field}' must be an integer")
                elif expected_type == 'number' and not isinstance(value, (int, float)):
                    raise SchemaValidationError(f"Field '{field}' must be a number")
                elif expected_type == 'boolean' and not isinstance(value, bool):
                    raise SchemaValidationError(f"Field '{field}' must be a boolean")
                elif expected_type == 'array' and not isinstance(value, list):
                    raise SchemaValidationError(f"Field '{field}' must be an array")
                elif expected_type == 'object' and not isinstance(value, dict):
                    raise SchemaValidationError(f"Field '{field}' must be an object")

    return True


def is_valid_uuid4(uuid_str: str) -> bool:
    """
    Validate if a string is a valid UUID4.

    Args:
        uuid_str: String to validate.

    Returns:
        True if valid UUID4, False otherwise.
    """
    if not uuid_str or not isinstance(uuid_str, str):
        return False

    # UUID4 pattern: 8-4-4-4-12 hex digits
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
    return bool(re.match(pattern, uuid_str.lower()))


# Specific schema loaders for common artifacts in this project

def load_config_schema() -> Dict[str, Any]:
    """Load the configuration schema."""
    schema_path = get_path('specs/001-llmxive-drift-detection/contracts/config.schema.yaml')
    # Convert .yaml to .json if needed, or load directly if json
    if schema_path.exists():
        # Try JSON first
        try:
            return load_json_file(schema_path.with_suffix('.json'))
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    # Fallback path
    return load_json_file(get_path('specs/001-llmxive-drift-detection/contracts/config.schema.json'))


def load_drift_result_schema() -> Dict[str, Any]:
    """Load the drift result schema."""
    return load_json_file(get_path('specs/001-llmxive-drift-detection/contracts/drift_result.schema.json'))


def validate_drift_result_schema(data: Dict[str, Any]) -> bool:
    """Validate data against the drift result schema."""
    schema = load_drift_result_schema()
    return validate_against_schema(data, schema)


def load_taxonomy_mapping_file(path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Load the taxonomy mapping file.

    Args:
        path: Optional path override. If None, uses default from config.

    Returns:
        Dictionary containing the taxonomy mapping.
    """
    if path is None:
        path = get_path('data/processed/taxonomy_mapping.json')
    return load_json_file(path)


def save_taxonomy_mapping_file(data: Dict[str, Any], path: Optional[Union[str, Path]] = None) -> None:
    """
    Save the taxonomy mapping file.

    Args:
        data: Taxonomy mapping data.
        path: Optional path override.
    """
    if path is None:
        path = get_path('data/processed/taxonomy_mapping.json')
    save_json_file(data, path)


def load_centroids_file(path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Load the centroids file.

    Args:
        path: Optional path override.

    Returns:
        Dictionary containing centroid data.
    """
    if path is None:
        path = get_path('data/processed/taxonomy_centroids.json')
    return load_json_file(path)


def save_centroids_file(data: Dict[str, Any], path: Optional[Union[str, Path]] = None) -> None:
    """
    Save the centroids file.

    Args:
        data: Centroid data.
        path: Optional path override.
    """
    if path is None:
        path = get_path('data/processed/taxonomy_centroids.json')
    save_json_file(data, path)


def load_drift_scores_file(path: Optional[Union[str, Path]] = None) -> List[Dict[str, Any]]:
    """
    Load the drift scores file (CSV).

    Args:
        path: Optional path override.

    Returns:
        List of dictionaries containing drift scores.
    """
    if path is None:
        path = get_path('data/processed/drift_scores.csv')
    return load_csv_file(path)


def save_drift_scores_file(data: List[Dict[str, Any]], path: Optional[Union[str, Path]] = None) -> None:
    """
    Save the drift scores file.

    Args:
        data: List of drift score records.
        path: Optional path override.
    """
    if path is None:
        path = get_path('data/processed/drift_scores.csv')
    save_csv_file(data, path)


def load_ground_truth_fixture(path: Optional[Union[str, Path]] = None) -> List[Dict[str, Any]]:
    """
    Load the ground truth fixture file.

    Args:
        path: Optional path override.

    Returns:
        List of dictionaries containing ground truth data.
    """
    if path is None:
        path = get_path('data/test/real_ground_truth_fixture.json')
    return load_json_file(path)


def save_ground_truth_fixture(data: List[Dict[str, Any]], path: Optional[Union[str, Path]] = None) -> None:
    """
    Save the ground truth fixture file.

    Args:
        data: List of ground truth records.
        path: Optional path override.
    """
    if path is None:
        path = get_path('data/test/real_ground_truth_fixture.json')
    save_json_file(data, path)