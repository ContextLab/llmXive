"""
Utility functions for contract validation, schema loading, and file I/O.

This module provides helpers for validating data against JSON schemas,
loading and saving JSON/CSV files, and performing contract checks.
"""
import json
import csv
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import yaml

from config import get_path


class SchemaValidationError(Exception):
    """Raised when data validation against a schema fails."""
    pass


def load_json_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a JSON file and return its contents as a dictionary.
    
    Args:
        file_path: Path to the JSON file.
        
    Returns:
        Dictionary containing the JSON data.
        
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
        file_path: Path where the JSON file will be saved.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_csv_file(file_path: Union[str, Path]) -> List[Dict[str, str]]:
    """
    Load a CSV file and return its contents as a list of dictionaries.
    
    Args:
        file_path: Path to the CSV file.
        
    Returns:
        List of dictionaries, one per row.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def save_csv_file(data: List[Dict[str, Any]], file_path: Union[str, Path]) -> None:
    """
    Save a list of dictionaries to a CSV file.
    
    Args:
        data: List of dictionaries to save.
        file_path: Path where the CSV file will be saved.
    """
    if not data:
        # Create empty file if no data
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        return
    
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = list(data[0].keys())
    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def load_schema(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a JSON schema from a file.
    
    Args:
        schema_path: Path to the schema file.
        
    Returns:
        Dictionary containing the schema definition.
    """
    return load_json_file(schema_path)


def validate_against_schema(data: Any, schema: Dict[str, Any]) -> bool:
    """
    Validate data against a JSON schema.
    
    This is a simplified validation that checks:
    - Required fields are present
    - Field types match (for simple types: string, integer, number, boolean, array, object)
    
    Args:
        data: Data to validate.
        schema: JSON schema definition.
        
    Returns:
        True if validation passes.
        
    Raises:
        SchemaValidationError: If validation fails.
    """
    def validate_type(value: Any, expected_type: str) -> bool:
        """Check if a value matches the expected JSON schema type."""
        type_mapping = {
            'string': str,
            'integer': int,
            'number': (int, float),
            'boolean': bool,
            'array': list,
            'object': dict,
            'null': type(None)
        }
        
        if expected_type not in type_mapping:
            return True  # Unknown type, skip validation
        
        expected_python_type = type_mapping[expected_type]
        return isinstance(value, expected_python_type)
    
    def validate_object(obj: Any, schema_obj: Dict[str, Any], path: str = "") -> None:
        """Recursively validate an object against a schema."""
        if not isinstance(obj, dict):
            if schema_obj.get('type') == 'object':
                raise SchemaValidationError(f"Expected object at {path}, got {type(obj).__name__}")
            return
        
        # Check required fields
        required = schema_obj.get('required', [])
        for field in required:
            if field not in obj:
                raise SchemaValidationError(f"Missing required field '{field}' at {path}")
        
        # Validate properties
        properties = schema_obj.get('properties', {})
        for key, value in obj.items():
            if key in properties:
                prop_schema = properties[key]
                current_path = f"{path}.{key}" if path else key
                
                # Check type
                if 'type' in prop_schema:
                    if not validate_type(value, prop_schema['type']):
                        raise SchemaValidationError(
                            f"Type mismatch at {current_path}: expected {prop_schema['type']}, got {type(value).__name__}"
                        )
                
                # Recursively validate nested objects
                if prop_schema.get('type') == 'object' and isinstance(value, dict):
                    validate_object(value, prop_schema, current_path)
                
                # Validate array items
                if prop_schema.get('type') == 'array' and isinstance(value, list):
                    items_schema = prop_schema.get('items', {})
                    for i, item in enumerate(value):
                        item_path = f"{current_path}[{i}]"
                        if items_schema.get('type') == 'object' and isinstance(item, dict):
                            validate_object(item, items_schema, item_path)
                        elif 'type' in items_schema:
                            if not validate_type(item, items_schema['type']):
                                raise SchemaValidationError(
                                    f"Type mismatch at {item_path}: expected {items_schema['type']}, got {type(item).__name__}"
                                )
    
    validate_object(data, schema)
    return True


def validate_schema(data: Any, schema_path: Union[str, Path]) -> bool:
    """
    Validate data against a JSON schema file.
    
    This is the main entry point for contract validation.
    
    Args:
        data: Data to validate.
        schema_path: Path to the JSON schema file.
        
    Returns:
        True if validation passes.
        
    Raises:
        SchemaValidationError: If validation fails.
        FileNotFoundError: If the schema file does not exist.
    """
    schema = load_schema(schema_path)
    return validate_against_schema(data, schema)


def is_valid_uuid4(uuid_string: str) -> bool:
    """
    Check if a string is a valid UUID4.
    
    Args:
        uuid_string: String to check.
        
    Returns:
        True if the string is a valid UUID4 format.
    """
    if not uuid_string:
        return False
    
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return bool(uuid_pattern.match(uuid_string))


# Convenience loaders for specific project schemas
def load_config_schema() -> Dict[str, Any]:
    """Load the configuration schema."""
    schema_path = get_path('specs/001-llmxive-drift-detection/contracts/config.schema.yaml')
    return load_schema(schema_path)


def load_drift_result_schema() -> Dict[str, Any]:
    """Load the drift result schema."""
    schema_path = get_path('specs/001-llmxive-drift-detection/contracts/drift_result.schema.yaml')
    return load_schema(schema_path)


def validate_drift_result_schema(data: Any) -> bool:
    """Validate data against the drift result schema."""
    schema = load_drift_result_schema()
    return validate_against_schema(data, schema)


def load_taxonomy_mapping_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Load a taxonomy mapping file."""
    return load_json_file(file_path)


def save_taxonomy_mapping_file(data: Dict[str, Any], file_path: Union[str, Path]) -> None:
    """Save a taxonomy mapping file."""
    save_json_file(data, file_path)


def load_centroids_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Load a centroids file."""
    return load_json_file(file_path)


def save_centroids_file(data: Dict[str, Any], file_path: Union[str, Path]) -> None:
    """Save a centroids file."""
    save_json_file(data, file_path)


def load_drift_scores_file(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Load a drift scores file (JSON format)."""
    return load_json_file(file_path)


def save_drift_scores_file(data: List[Dict[str, Any]], file_path: Union[str, Path]) -> None:
    """Save a drift scores file (JSON format)."""
    save_json_file(data, file_path)


def load_ground_truth_fixture(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Load a ground truth fixture file."""
    return load_json_file(file_path)


def save_ground_truth_fixture(data: List[Dict[str, Any]], file_path: Union[str, Path]) -> None:
    """Save a ground truth fixture file."""
    save_json_file(data, file_path)
