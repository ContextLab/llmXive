"""
Schema validation helpers for YAML/JSON configuration and data files.

Provides utilities to load, parse, and validate configuration files
against defined schemas, ensuring data integrity for the research pipeline.
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
        ValidationError: If file cannot be read or parsed.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise ValidationError(f"YAML file not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            # Handle empty files
            if data is None:
                return {}
            if not isinstance(data, Mapping):
                raise ValidationError(f"YAML root must be a mapping (dict), got {type(data)}")
            return dict(data)
    except yaml.YAMLError as e:
        raise ValidationError(f"Failed to parse YAML file {file_path}: {e}")
    except Exception as e:
        raise ValidationError(f"Error reading YAML file {file_path}: {e}")


def load_json(path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load and parse a JSON file.
    
    Args:
        path: Path to the JSON file.
        
    Returns:
        Parsed dictionary content.
        
    Raises:
        ValidationError: If file cannot be read or parsed.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise ValidationError(f"JSON file not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, Mapping):
                raise ValidationError(f"JSON root must be a mapping (dict), got {type(data)}")
            return dict(data)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Failed to parse JSON file {file_path}: {e}")
    except Exception as e:
        raise ValidationError(f"Error reading JSON file {file_path}: {e}")


def validate_type(value: Any, expected_type: type, field_name: str = "value") -> None:
    """
    Validate that a value matches the expected type.
    
    Args:
        value: The value to check.
        expected_type: The expected Python type.
        field_name: Name of the field for error messaging.
        
    Raises:
        ValidationError: If type mismatch occurs.
    """
    if not isinstance(value, expected_type):
        raise ValidationError(
            f"Field '{field_name}' must be of type {expected_type.__name__}, "
            f"got {type(value).__name__}"
        )


def validate_required_fields(data: Dict[str, Any], required_fields: List[str], context: str = "data") -> None:
    """
    Validate that all required fields are present in a dictionary.
    
    Args:
        data: The dictionary to check.
        required_fields: List of required field names.
        context: Context name for error messaging.
        
    Raises:
        ValidationError: If any required field is missing.
    """
    missing = [f for f in required_fields if f not in data]
    if missing:
        raise ValidationError(
            f"Missing required fields in {context}: {', '.join(missing)}"
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
        field_name: Name of the field for error messaging.
        
    Raises:
        ValidationError: If value is out of range.
    """
    if min_val is not None and value < min_val:
        raise ValidationError(
            f"Field '{field_name}' value {value} is below minimum {min_val}"
        )
    if max_val is not None and value > max_val:
        raise ValidationError(
            f"Field '{field_name}' value {value} is above maximum {max_val}"
        )


def validate_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """
    Validate a dictionary against a simple schema definition.
    
    Schema format:
    {
        "field_name": {
            "type": <type>,
            "required": <bool>,
            "min": <number>,
            "max": <number>,
            "validator": <callable>
        }
    }
    
    Args:
        data: The data dictionary to validate.
        schema: The schema definition dictionary.
        
    Raises:
        ValidationError: If validation fails.
    """
    for field_name, rules in schema.items():
        is_required = rules.get("required", False)
        
        if field_name not in data:
            if is_required:
                raise ValidationError(f"Missing required field: {field_name}")
            continue
        
        value = data[field_name]
        
        # Type check
        if "type" in rules:
            validate_type(value, rules["type"], field_name)
        
        # Range check
        if "min" in rules or "max" in rules:
            if not isinstance(value, (int, float)):
                raise ValidationError(
                    f"Field '{field_name}' must be numeric for range validation"
                )
            validate_range(value, rules.get("min"), rules.get("max"), field_name)
        
        # Custom validator
        if "validator" in rules:
            validator = rules["validator"]
            if not callable(validator):
                raise ValidationError(f"Validator for '{field_name}' must be callable")
            try:
                validator(value)
            except Exception as e:
                raise ValidationError(f"Custom validation failed for '{field_name}': {e}")


def validate_config_file(
    config_path: Union[str, Path],
    schema: Optional[Dict[str, Any]] = None,
    required_fields: Optional[List[str]] = None,
    file_type: str = "yaml"
) -> Dict[str, Any]:
    """
    Load and validate a configuration file against a schema or required fields.
    
    Args:
        config_path: Path to the configuration file.
        schema: Optional schema definition for validation.
        required_fields: Optional list of required field names.
        file_type: Type of file ('yaml' or 'json').
        
    Returns:
        The loaded configuration dictionary.
        
    Raises:
        ValidationError: If loading or validation fails.
    """
    # Load the file
    if file_type.lower() == "yaml":
        config = load_yaml(config_path)
    elif file_type.lower() == "json":
        config = load_json(config_path)
    else:
        raise ValidationError(f"Unsupported file type: {file_type}")
    
    # Validate required fields
    if required_fields:
        validate_required_fields(config, required_fields, context=f"config file {config_path}")
    
    # Validate against schema
    if schema:
        validate_schema(config, schema)
    
    return config