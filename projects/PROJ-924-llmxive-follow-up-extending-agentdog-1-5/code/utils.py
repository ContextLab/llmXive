"""
Utility functions for contract validation, schema loading, and file I/O.
"""
import json
import csv
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from config import get_path, ensure_directories


class SchemaValidationError(Exception):
    """Raised when data fails schema validation."""
    pass


def load_json_file(path: Union[str, Path]) -> Dict[str, Any]:
    """Load and parse a JSON file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(data: Dict[str, Any], path: Union[str, Path]) -> None:
    """Save data to a JSON file."""
    path = Path(path)
    ensure_directories([path.parent])
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_csv_file(path: Union[str, Path], delimiter: str = ',') -> List[Dict[str, Any]]:
    """Load a CSV file and return a list of dictionaries."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        return list(reader)


def save_csv_file(data: List[Dict[str, Any]], path: Union[str, Path], delimiter: str = ',') -> None:
    """Save a list of dictionaries to a CSV file."""
    path = Path(path)
    ensure_directories([path.parent])
    if not data:
        # Write empty file with no headers if data is empty
        with open(path, 'w', encoding='utf-8') as f:
            pass
        return

    fieldnames = list(data[0].keys())
    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
        writer.writeheader()
        writer.writerows(data)


def load_schema(schema_name: str) -> Dict[str, Any]:
    """
    Load a JSON schema by name from the specs directory.
    Expected path: <project_root>/specs/<schema_name>.json
    """
    base_dir = get_path("specs")
    schema_path = Path(base_dir) / f"{schema_name}.json"
    return load_json_file(schema_path)


def validate_against_schema(data: Union[Dict[str, Any], List[Dict[str, Any]]], schema: Dict[str, Any]) -> bool:
    """
    Validate data against a JSON schema.
    This is a simplified validator that checks required keys and types.
    For full JSON Schema validation, jsonschema library would be used,
    but we implement a lightweight version here to avoid extra dependencies
    if not strictly necessary for the core logic.
    """
    # Basic type checking for dict/list structures
    if "type" in schema:
        expected_type = schema["type"]
        if expected_type == "object" and not isinstance(data, dict):
            return False
        if expected_type == "array" and not isinstance(data, list):
            return False

    # Check required fields
    if "required" in schema and isinstance(data, dict):
        for field in schema["required"]:
            if field not in data:
                raise SchemaValidationError(f"Missing required field: {field}")

    # Check properties if defined
    if "properties" in schema and isinstance(data, dict):
        for prop, prop_schema in schema["properties"].items():
            if prop in data:
                value = data[prop]
                if "type" in prop_schema:
                    if prop_schema["type"] == "string" and not isinstance(value, str):
                        raise SchemaValidationError(f"Field '{prop}' must be a string")
                    if prop_schema["type"] == "integer" and not isinstance(value, int):
                        raise SchemaValidationError(f"Field '{prop}' must be an integer")
                    if prop_schema["type"] == "number" and not isinstance(value, (int, float)):
                        raise SchemaValidationError(f"Field '{prop}' must be a number")
                    if prop_schema["type"] == "boolean" and not isinstance(value, bool):
                        raise SchemaValidationError(f"Field '{prop}' must be a boolean")

    return True


def validate_schema(data: Union[Dict[str, Any], List[Dict[str, Any]]], schema_name: str) -> bool:
    """
    Load a schema by name and validate data against it.
    Raises SchemaValidationError if validation fails.
    """
    schema = load_schema(schema_name)
    return validate_against_schema(data, schema)


def is_valid_uuid4(uuid_string: str) -> bool:
    """Check if a string is a valid UUID4."""
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
    return bool(re.match(pattern, uuid_string, re.IGNORECASE))


# Schema loaders for specific use cases
def load_config_schema() -> Dict[str, Any]:
    """Load the configuration schema."""
    return load_schema("config_schema")


def load_drift_result_schema() -> Dict[str, Any]:
    """Load the drift result schema."""
    return load_schema("drift_result_schema")


def validate_drift_result_schema(data: List[Dict[str, Any]]) -> bool:
    """Validate drift result data against its schema."""
    return validate_schema(data, "drift_result_schema")


def load_taxonomy_mapping_file(path: Union[str, Path]) -> Dict[str, Any]:
    """Load a taxonomy mapping file."""
    return load_json_file(path)


def save_taxonomy_mapping_file(data: Dict[str, Any], path: Union[str, Path]) -> None:
    """Save a taxonomy mapping file."""
    save_json_file(data, path)


def load_centroids_file(path: Union[str, Path]) -> Dict[str, Any]:
    """Load a centroids file."""
    return load_json_file(path)


def save_centroids_file(data: Dict[str, Any], path: Union[str, Path]) -> None:
    """Save a centroids file."""
    save_json_file(data, path)


def load_drift_scores_file(path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Load a drift scores file (CSV)."""
    return load_csv_file(path)


def save_drift_scores_file(data: List[Dict[str, Any]], path: Union[str, Path]) -> None:
    """Save a drift scores file (CSV)."""
    save_csv_file(data, path)


def load_ground_truth_fixture(path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Load a ground truth fixture file."""
    return load_json_file(path)


def save_ground_truth_fixture(data: List[Dict[str, Any]], path: Union[str, Path]) -> None:
    """Save a ground truth fixture file."""
    save_json_file(data, path)
