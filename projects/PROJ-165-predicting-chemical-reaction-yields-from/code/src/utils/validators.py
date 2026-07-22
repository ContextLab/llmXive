"""
Schema validation helpers for YAML/JSON configuration and data files.

This module provides utilities to validate structured data against defined schemas,
ensuring type safety, required field presence, and value ranges before processing.
"""
import json
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable
from collections.abc import Mapping


class ValidationError(Exception):
    """Custom exception for schema validation failures."""
    pass


def load_yaml(path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load and parse a YAML file.
    
    Args:
        path: Path to the YAML file.
        
    Returns:
        Parsed dictionary content.
        
    Raises:
        ValidationError: If the file cannot be read or parsed.
        FileNotFoundError: If the file does not exist.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {path}")
        
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if data is None:
                return {}
            if not isinstance(data, Mapping):
                raise ValidationError(f"YAML root must be a mapping, got {type(data).__name__}")
            return dict(data)
    except yaml.YAMLError as e:
        raise ValidationError(f"Failed to parse YAML: {e}")


def load_json(path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load and parse a JSON file.
    
    Args:
        path: Path to the JSON file.
        
    Returns:
        Parsed dictionary content.
        
    Raises:
        ValidationError: If the file cannot be read or parsed.
        FileNotFoundError: If the file does not exist.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")
        
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, Mapping):
                raise ValidationError(f"JSON root must be a mapping, got {type(data).__name__}")
            return dict(data)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Failed to parse JSON: {e}")


def validate_type(value: Any, expected_type: type, field_name: str) -> None:
    """
    Validate that a value matches the expected type.
    
    Args:
        value: The value to check.
        expected_type: The expected Python type.
        field_name: Name of the field for error reporting.
        
    Raises:
        ValidationError: If the type does not match.
    """
    if not isinstance(value, expected_type):
        raise ValidationError(
            f"Field '{field_name}' expected type '{expected_type.__name__}', "
            f"got '{type(value).__name__}'"
        )


def validate_required_fields(data: Dict[str, Any], required_fields: List[str], context: str = "") -> None:
    """
    Validate that all required fields are present in a dictionary.
    
    Args:
        data: The dictionary to check.
        required_fields: List of field names that must be present.
        context: Optional context string for error messages.
        
    Raises:
        ValidationError: If any required field is missing.
    """
    missing = [f for f in required_fields if f not in data]
    if missing:
        context_str = f" in '{context}'" if context else ""
        raise ValidationError(
            f"Missing required field{ 's' if len(missing) > 1 else ''}{context_str}: {', '.join(missing)}"
        )


def validate_range(
    value: Union[int, float],
    min_val: Optional[Union[int, float]] = None,
    max_val: Optional[Union[int, float]] = None,
    field_name: str = "value"
) -> None:
    """
    Validate that a numeric value is within a specified range.
    
    Args:
        value: The numeric value to check.
        min_val: Minimum allowed value (inclusive).
        max_val: Maximum allowed value (inclusive).
        field_name: Name of the field for error reporting.
        
    Raises:
        ValidationError: If the value is out of range.
    """
    if min_val is not None and value < min_val:
        raise ValidationError(f"Field '{field_name}' must be >= {min_val}, got {value}")
    if max_val is not None and value > max_val:
        raise ValidationError(f"Field '{field_name}' must be <= {max_val}, got {value}")


def validate_schema(
    data: Dict[str, Any],
    schema: Dict[str, Any],
    strict: bool = False
) -> None:
    """
    Validate a dictionary against a schema definition.
    
    The schema is a dictionary where keys are field names and values are:
    - A type object (e.g., `str`, `int`) for simple type checking.
    - A dictionary with 'type' and optional 'required', 'min', 'max', 'choices' keys.
    
    Args:
        data: The data dictionary to validate.
        schema: The schema definition.
        strict: If True, raise an error if data contains keys not in the schema.
        
    Raises:
        ValidationError: If validation fails.
    """
    for field_name, definition in schema.items():
        if field_name not in data:
            # Check if required
            is_required = False
            field_type = None
            
            if isinstance(definition, dict):
                is_required = definition.get('required', False)
                field_type = definition.get('type')
            else:
                field_type = definition
                
            if is_required:
                raise ValidationError(f"Missing required field '{field_name}'")
            continue
        
        value = data[field_name]
        
        # Determine field constraints
        is_required = True
        field_type = None
        min_val = None
        max_val = None
        choices = None
        
        if isinstance(definition, dict):
            is_required = definition.get('required', True)
            field_type = definition.get('type')
            min_val = definition.get('min')
            max_val = definition.get('max')
            choices = definition.get('choices')
        else:
            field_type = definition
        
        # Type validation
        if field_type is not None:
            validate_type(value, field_type, field_name)
        
        # Range validation
        if isinstance(value, (int, float)):
            validate_range(value, min_val, max_val, field_name)
        
        # Choices validation
        if choices is not None:
            if value not in choices:
                raise ValidationError(
                    f"Field '{field_name}' must be one of {choices}, got {value}"
                )
    
    # Strict mode: check for extra keys
    if strict:
        extra_keys = set(data.keys()) - set(schema.keys())
        if extra_keys:
            raise ValidationError(f"Unexpected fields in data: {', '.join(extra_keys)}")


def validate_config_file(
    path: Union[str, Path],
    schema: Dict[str, Any],
    file_type: str = "yaml"
) -> Dict[str, Any]:
    """
    Load and validate a configuration file against a schema.
    
    Args:
        path: Path to the config file.
        schema: Schema definition.
        file_type: 'yaml' or 'json'.
        
    Returns:
        The validated and parsed configuration dictionary.
        
    Raises:
        ValidationError: If loading or validation fails.
    """
    if file_type.lower() == "yaml":
        data = load_yaml(path)
    elif file_type.lower() == "json":
        data = load_json(path)
    else:
        raise ValidationError(f"Unsupported file type: {file_type}")
        
    validate_schema(data, schema)
    return data