"""
Utility functions for contract validation, schema loading, and file I/O.
"""
import json
import csv
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from config import get_path


class SchemaValidationError(Exception):
    """Raised when data fails schema validation."""
    pass


def load_json_file(path: Union[str, Path]) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(path: Union[str, Path], data: Dict[str, Any]) -> None:
    """Save a dictionary to a JSON file."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_csv_file(path: Union[str, Path]) -> List[Dict[str, str]]:
    """Load a CSV file and return its contents as a list of dictionaries."""
    with open(path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        return list(reader)


def save_csv_file(path: Union[str, Path], data: List[Dict[str, str]]) -> None:
    """Save a list of dictionaries to a CSV file."""
    if not data:
        # Write empty file if no data
        with open(path, 'w', encoding='utf-8', newline='') as f:
            pass
        return

    fieldnames = list(data[0].keys())
    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def load_schema(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """Load a JSON schema from a file."""
    return load_json_file(schema_path)


def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate data against a JSON schema.
    This is a simplified validator for basic contract checking.
    For full JSON Schema validation, jsonschema library would be used,
    but we implement basic checks here to avoid extra dependencies if not needed.
    """
    # Basic type check
    if 'type' in schema:
        expected_type = schema['type']
        if expected_type == 'object' and not isinstance(data, dict):
            raise SchemaValidationError(f"Expected object, got {type(data).__name__}")
        elif expected_type == 'array' and not isinstance(data, list):
            raise SchemaValidationError(f"Expected array, got {type(data).__name__}")
        elif expected_type == 'string' and not isinstance(data, str):
            raise SchemaValidationError(f"Expected string, got {type(data).__name__}")
        elif expected_type == 'number' and not isinstance(data, (int, float)):
            raise SchemaValidationError(f"Expected number, got {type(data).__name__}")
        elif expected_type == 'integer' and not isinstance(data, int):
            raise SchemaValidationError(f"Expected integer, got {type(data).__name__}")
        elif expected_type == 'boolean' and not isinstance(data, bool):
            raise SchemaValidationError(f"Expected boolean, got {type(data).__name__}")

    # Check required fields
    if 'required' in schema and isinstance(data, dict):
        for field in schema['required']:
            if field not in data:
                raise SchemaValidationError(f"Missing required field: {field}")

    # Check properties
    if 'properties' in schema and isinstance(data, dict):
        for key, value_schema in schema['properties'].items():
            if key in data:
                # Recursively validate nested structures if needed
                # For now, we do a simple type check if type is specified
                if 'type' in value_schema:
                    val = data[key]
                    exp_type = value_schema['type']
                    if exp_type == 'string' and not isinstance(val, str):
                        raise SchemaValidationError(f"Field '{key}' expected string, got {type(val).__name__}")
                    elif exp_type == 'number' and not isinstance(val, (int, float)):
                        raise SchemaValidationError(f"Field '{key}' expected number, got {type(val).__name__}")
                    elif exp_type == 'integer' and not isinstance(val, int):
                        raise SchemaValidationError(f"Field '{key}' expected integer, got {type(val).__name__}")
                    elif exp_type == 'boolean' and not isinstance(val, bool):
                        raise SchemaValidationError(f"Field '{key}' expected boolean, got {type(val).__name__}")
                    elif exp_type == 'array' and not isinstance(val, list):
                        raise SchemaValidationError(f"Field '{key}' expected array, got {type(val).__name__}")
                    elif exp_type == 'object' and not isinstance(val, dict):
                        raise SchemaValidationError(f"Field '{key}' expected object, got {type(val).__name__}")

    return True


def validate_schema(data: Dict[str, Any], schema_path: Union[str, Path]) -> bool:
    """
    Validate data against a schema file.
    Raises SchemaValidationError if validation fails.
    Returns True if valid.
    """
    schema = load_schema(schema_path)
    return validate_against_schema(data, schema)


def is_valid_uuid4(uuid_str: str) -> bool:
    """Check if a string is a valid UUID4."""
    pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$', re.I)
    return pattern.match(uuid_str) is not None


# Specific schema loaders for project artifacts
def load_config_schema() -> Dict[str, Any]:
    """Load the config schema."""
    schema_path = get_path('specs/contracts/config.schema.json')
    return load_schema(schema_path)


def load_drift_result_schema() -> Dict[str, Any]:
    """Load the drift result schema."""
    schema_path = get_path('specs/contracts/drift_result.schema.yaml')
    # Note: If the file is YAML, we might need to parse it differently.
    # For now, assuming it's JSON or we handle YAML if pyyaml is available.
    # The task mentions .yaml extension, but we'll try to load as JSON first.
    # If it fails, we might need to import yaml.
    try:
        return load_json_file(schema_path)
    except json.JSONDecodeError:
        # Fallback: try to read as simple key-value if it's a simple YAML
        # In a real scenario, we'd use pyyaml.
        raise SchemaValidationError("Schema file is not valid JSON. YAML support requires pyyaml.")


def validate_drift_result_schema(data: Dict[str, Any]) -> bool:
    """Validate data against the drift result schema."""
    schema = load_drift_result_schema()
    return validate_against_schema(data, schema)


# File type specific loaders
def load_taxonomy_mapping_file(path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Load a taxonomy mapping file."""
    if path is None:
        path = get_path('data/raw/taxonomy_agentdog.json')
    return load_json_file(path)


def save_taxonomy_mapping_file(data: Dict[str, Any], path: Optional[Union[str, Path]] = None) -> None:
    """Save a taxonomy mapping file."""
    if path is None:
        path = get_path('data/raw/taxonomy_agentdog.json')
    save_json_file(path, data)


def load_centroids_file(path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Load a centroids file."""
    if path is None:
        path = get_path('data/processed/taxonomy_centroids.json')
    return load_json_file(path)


def save_centroids_file(data: Dict[str, Any], path: Optional[Union[str, Path]] = None) -> None:
    """Save a centroids file."""
    if path is None:
        path = get_path('data/processed/taxonomy_centroids.json')
    save_json_file(path, data)


def load_drift_scores_file(path: Optional[Union[str, Path]] = None) -> List[Dict[str, Any]]:
    """Load a drift scores file (CSV)."""
    if path is None:
        path = get_path('data/processed/drift_scores.csv')
    return load_csv_file(path)


def save_drift_scores_file(data: List[Dict[str, Any]], path: Optional[Union[str, Path]] = None) -> None:
    """Save a drift scores file (CSV)."""
    if path is None:
        path = get_path('data/processed/drift_scores.csv')
    save_csv_file(path, data)


def load_ground_truth_fixture(path: Optional[Union[str, Path]] = None) -> List[Dict[str, Any]]:
    """Load a ground truth fixture file."""
    if path is None:
        path = get_path('data/test/real_ground_truth_fixture.json')
    return load_json_file(path)


def save_ground_truth_fixture(data: List[Dict[str, Any]], path: Optional[Union[str, Path]] = None) -> None:
    """Save a ground truth fixture file."""
    if path is None:
        path = get_path('data/test/real_ground_truth_fixture.json')
    save_json_file(path, data)
