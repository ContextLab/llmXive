"""Contract and schema validation utilities."""
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from utils.logging import get_logger

logger = get_logger("contract_validator")

def validate_schema(data: Dict[str, Any], schema_path: str) -> bool:
    """
    Validate data against a JSON schema.
    
    Args:
        data: The data to validate.
        schema_path: Path to the JSON schema file.
    
    Returns:
        bool: True if data is valid against the schema, False otherwise.
            Errors are logged but not returned; this function returns a simple bool.
    
    Raises:
        FileNotFoundError: If the schema file does not exist.
        json.JSONDecodeError: If the schema file contains invalid JSON.
        ImportError: If the jsonschema library is not installed.
    """
    try:
        import jsonschema
    except ImportError:
        logger.error("jsonschema library not found. Please install it.")
        raise ImportError("jsonschema library missing. Please install it via requirements.txt.")

    try:
        with open(schema_path, 'r') as f:
            schema = json.load(f)
    except FileNotFoundError:
        logger.error(f"Schema file not found: {schema_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in schema file: {e}")
        raise

    try:
        jsonschema.validate(instance=data, schema=schema)
        logger.debug(f"Data validated successfully against schema: {schema_path}")
        return True
    except jsonschema.ValidationError as e:
        logger.error(f"Validation error: {e.message}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        return False

def validate_contract(data: Dict[str, Any], contract_rules: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """
    Validate data against a list of custom contract rules.
    
    Rules are expected to be dicts like:
    {"field": "name", "type": "str", "required": True}
    
    Args:
        data: The data to validate.
        contract_rules: List of rule definitions.
    
    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []
    
    for rule in contract_rules:
        field = rule.get("field")
        required = rule.get("required", False)
        expected_type = rule.get("type")
        
        if field not in data:
            if required:
                errors.append(f"Missing required field: {field}")
            continue
        
        value = data[field]
        if expected_type:
            # Map string types to python types
            type_map = {
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict
            }
            target_type = type_map.get(expected_type)
            if target_type and not isinstance(value, target_type):
                errors.append(f"Field '{field}' has wrong type. Expected {expected_type}, got {type(value).__name__}")
    
    return len(errors) == 0, errors