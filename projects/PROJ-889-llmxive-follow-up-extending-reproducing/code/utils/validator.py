"""
Data validation utilities using JSON Schema.
Validates trajectory and metrics data against the contracts defined in contracts/
"""
import json
import jsonschema
from pathlib import Path
from typing import Any, Dict, List

from code.config import get_project_root
from code.utils.io_utils import read_json


def load_schema(schema_name: str) -> Dict[str, Any]:
    """Load a JSON schema from the contracts directory."""
    project_root = get_project_root()
    schema_path = project_root / "contracts" / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    return read_json(str(schema_path))


def validate_trajectory_data(data: Dict[str, Any]) -> bool:
    """
    Validate trajectory data against trajectory_schema.json.
    
    Args:
        data: The parsed JSON data to validate.
        
    Returns:
        True if valid.
        
    Raises:
        jsonschema.exceptions.ValidationError: If validation fails.
    """
    schema = load_schema("trajectory_schema.json")
    jsonschema.validate(instance=data, schema=schema)
    return True


def validate_metrics_data(data: Dict[str, Any]) -> bool:
    """
    Validate metrics data against metrics_schema.json.
    
    Args:
        data: The parsed JSON data to validate.
        
    Returns:
        True if valid.
        
    Raises:
        jsonschema.exceptions.ValidationError: If validation fails.
    """
    schema = load_schema("metrics_schema.json")
    jsonschema.validate(instance=data, schema=schema)
    return True


def validate_file_against_schema(file_path: str, schema_name: str) -> bool:
    """
    Validate a JSON file against a specific schema.
    
    Args:
        file_path: Path to the JSON file.
        schema_name: Name of the schema file in contracts/.
        
    Returns:
        True if valid.
        
    Raises:
        FileNotFoundError: If file or schema not found.
        jsonschema.exceptions.ValidationError: If validation fails.
    """
    data = read_json(file_path)
    if schema_name == "trajectory_schema.json":
        return validate_trajectory_data(data)
    elif schema_name == "metrics_schema.json":
        return validate_metrics_data(data)
    else:
        raise ValueError(f"Unknown schema: {schema_name}")
