"""
Schema validation utilities for the neuro-symbolic learning networks project.

This module provides functions to validate data against the JSON Schema
definitions located in the `contracts/` directory.
"""
import json
import os
from typing import Any, Dict, List, Tuple

try:
    import jsonschema
    from jsonschema import validate, ValidationError, Draft7Validator
except ImportError:
    raise ImportError(
        "The 'jsonschema' package is required for validation. "
        "Install it via: pip install jsonschema"
    )

# Base path for schema files relative to project root
# Project structure: code/utils/validation.py -> ../../contracts/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCHEMAS_PATH = os.path.join(PROJECT_ROOT, "contracts")

def _load_schema(schema_name: str) -> Dict[str, Any]:
    """Load a JSON schema from the contracts directory."""
    schema_path = os.path.join(SCHEMAS_PATH, schema_name)
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_problem(data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate a problem record against problem.schema.yaml.
    
    Args:
        data: The problem dictionary to validate.
    
    Returns:
        Tuple of (is_valid: bool, error_message: str).
        If valid, error_message is empty.
    """
    try:
        schema = _load_schema("problem.schema.yaml")
        validate(instance=data, schema=schema)
        return True, ""
    except ValidationError as e:
        return False, str(e.message)

def validate_explanation(data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate an explanation record against explanation.schema.yaml.
    
    Args:
        data: The explanation dictionary to validate.
    
    Returns:
        Tuple of (is_valid: bool, error_message: str).
    """
    try:
        schema = _load_schema("explanation.schema.yaml")
        validate(instance=data, schema=schema)
        return True, ""
    except ValidationError as e:
        return False, str(e.message)

def validate_simulation_log(data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate a simulation log record against simulation_log.schema.yaml.
    
    Args:
        data: The log record dictionary to validate.
    
    Returns:
        Tuple of (is_valid: bool, error_message: str).
    """
    try:
        schema = _load_schema("simulation_log.schema.yaml")
        validate(instance=data, schema=schema)
        return True, ""
    except ValidationError as e:
        return False, str(e.message)

def validate_batch(data_list: List[Dict[str, Any]], validator_func) -> List[Tuple[int, bool, str]]:
    """
    Validate a list of records using a specific validator function.
    
    Args:
        data_list: List of records to validate.
        validator_func: Function like validate_problem that takes a dict and returns (bool, str).
    
    Returns:
        List of tuples (index, is_valid, error_message).
    """
    results = []
    for i, item in enumerate(data_list):
        is_valid, msg = validator_func(item)
        results.append((i, is_valid, msg))
    return results