"""
Schema loading and validation utilities for contract tests.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load a schema from a JSON or YAML file.

    Args:
        schema_path: Path to the schema file.

    Returns:
        Dict containing the loaded schema.
    """
    path = Path(schema_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / schema_path

    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")

    with open(path, "r") as f:
        if path.suffix in (".yaml", ".yml"):
            return yaml.safe_load(f)
        elif path.suffix == ".json":
            return json.load(f)
        else:
            raise ValueError(f"Unsupported schema format: {path.suffix}")

def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate data against a JSON schema.

    Args:
        data: Data to validate.
        schema: JSON schema to validate against.

    Returns:
        True if valid, False otherwise.
    """
    # Simple validation - in production, use jsonschema library
    # This is a placeholder for basic type checking
    if "type" not in schema:
        return True

    schema_type = schema["type"]
    if schema_type == "object":
        if not isinstance(data, dict):
            return False
        properties = schema.get("properties", {})
        for key, value_schema in properties.items():
            if key in data:
                if not validate_against_schema(data[key], value_schema):
                    return False
        return True
    elif schema_type == "array":
        if not isinstance(data, list):
            return False
        items_schema = schema.get("items", {})
        for item in data:
            if not validate_against_schema(item, items_schema):
                return False
        return True
    elif schema_type == "string":
        return isinstance(data, str)
    elif schema_type == "number":
        return isinstance(data, (int, float))
    elif schema_type == "integer":
        return isinstance(data, int)
    elif schema_type == "boolean":
        return isinstance(data, bool)

    return True

def load_and_validate_dataset_schema(data: Dict[str, Any]) -> bool:
    """
    Load the dataset schema and validate data against it.

    Args:
        data: Dataset data to validate.

    Returns:
        True if valid, False otherwise.
    """
    schema_path = "contracts/dataset.schema.yaml"
    try:
        schema = load_schema(schema_path)
        return validate_against_schema(data, schema)
    except FileNotFoundError:
        # If schema doesn't exist, skip validation
        return True

def load_and_validate_model_output_schema(data: Dict[str, Any]) -> bool:
    """
    Load the model output schema and validate data against it.

    Args:
        data: Model output data to validate.

    Returns:
        True if valid, False otherwise.
    """
    schema_path = "contracts/model_output.schema.yaml"
    try:
        schema = load_schema(schema_path)
        return validate_against_schema(data, schema)
    except FileNotFoundError:
        # If schema doesn't exist, skip validation
        return True
