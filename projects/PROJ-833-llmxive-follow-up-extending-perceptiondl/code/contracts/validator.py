"""
Utility to validate JSON data against the defined YAML schemas.
"""
import json
import yaml
from pathlib import Path
from jsonschema import validate, ValidationError, Draft7Validator
import os

# Ensure we can locate the schema files relative to this module
_SCHEMAS_DIR = Path(__file__).parent.parent.parent / "contracts"

def _load_schema(schema_name: str) -> dict:
    """Load a schema from the contracts directory."""
    schema_path = _SCHEMAS_DIR / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

def validate_synthetic_image(data: dict) -> bool:
    """
    Validate a synthetic image annotation dictionary against the schema.
    
    Args:
        data: Dictionary containing image annotation data.
        
    Returns:
        True if valid.
        
    Raises:
        ValidationError: If the data does not match the schema.
    """
    schema = _load_schema("synthetic_image.schema.yaml")
    validate(instance=data, schema=schema)
    return True

def validate_regression_result(data: dict) -> bool:
    """
    Validate a regression result dictionary against the schema.
    
    Args:
        data: Dictionary containing regression analysis results.
        
    Returns:
        True if valid.
        
    Raises:
        ValidationError: If the data does not match the schema.
    """
    schema = _load_schema("regression_result.schema.yaml")
    validate(instance=data, schema=schema)
    return True

def validate_file(file_path: str, schema_type: str) -> bool:
    """
    Validate a JSON file against a specific schema type.
    
    Args:
        file_path: Path to the JSON file.
        schema_type: Either 'synthetic_image' or 'regression_result'.
        
    Returns:
        True if valid.
        
    Raises:
        FileNotFoundError: If the JSON file or schema is missing.
        ValidationError: If the JSON content is invalid.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    with open(file_path, "r") as f:
        data = json.load(f)
    
    if schema_type == "synthetic_image":
        return validate_synthetic_image(data)
    elif schema_type == "regression_result":
        return validate_regression_result(data)
    else:
        raise ValueError(f"Unknown schema type: {schema_type}")
