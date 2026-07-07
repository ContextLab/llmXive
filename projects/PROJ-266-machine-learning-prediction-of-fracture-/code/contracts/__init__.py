"""
Contract validation utilities for dataset and evaluation schemas.

This module provides validation functions to ensure data and evaluation
outputs conform to the defined JSON Schema specifications.
"""

import json
import yaml
from pathlib import Path
from typing import Any, Dict, Tuple

try:
    import jsonschema
    from jsonschema import validate, ValidationError
except ImportError:
    jsonschema = None
    ValidationError = Exception

SCHEMA_DIR = Path(__file__).parent.parent.parent / "contracts"

def load_schema(schema_name: str) -> Dict[str, Any]:
    """Load a JSON Schema from the contracts directory."""
    schema_path = SCHEMA_DIR / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

def validate_dataset(data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate dataset structure against dataset_schema.schema.yaml.
    
    Args:
        data: Dictionary containing dataset metadata and samples
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if jsonschema is None:
        raise ImportError(
            "jsonschema package is required for validation. "
            "Install with: pip install jsonschema"
        )
    
    schema = load_schema("dataset_schema.schema.yaml")
    try:
        validate(instance=data, schema=schema)
        return True, ""
    except ValidationError as e:
        return False, f"Dataset validation failed: {e.message}"

def validate_evaluation(metrics: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate evaluation results against evaluation_schema.schema.yaml.
    
    Args:
        metrics: Dictionary containing evaluation metrics and metadata
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if jsonschema is None:
        raise ImportError(
            "jsonschema package is required for validation. "
            "Install with: pip install jsonschema"
        )
    
    schema = load_schema("evaluation_schema.schema.yaml")
    try:
        validate(instance=metrics, schema=schema)
        return True, ""
    except ValidationError as e:
        return False, f"Evaluation validation failed: {e.message}"

def validate_file(path: Path, schema_name: str) -> Tuple[bool, str]:
    """
    Validate a JSON file against a schema.
    
    Args:
        path: Path to the JSON file
        schema_name: Name of the schema file in contracts/
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not path.exists():
        return False, f"File not found: {path}"
    
    try:
        with open(path, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"
    
    if schema_name == "dataset_schema.schema.yaml":
        return validate_dataset(data)
    elif schema_name == "evaluation_schema.schema.yaml":
        return validate_evaluation(data)
    else:
        return False, f"Unknown schema: {schema_name}"
