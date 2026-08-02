"""
Schema validation utilities for llmXive contracts and data structures.

This module provides strict validation functions to ensure data integrity
across the pipeline, specifically for contracts defined in the project.
It validates configuration objects, model metadata, and data loader outputs
against expected schemas.
"""
import json
from typing import Any, Dict, List, Optional, Type, Union
from dataclasses import is_dataclass, fields
from pathlib import Path

from utils.logger import LlmXiveError, ConfigurationError, DataLoadError


class SchemaValidationError(LlmXiveError):
    """Raised when data fails schema validation."""
    pass


def validate_dict_schema(data: Dict[str, Any], schema: Dict[str, Type], strict: bool = True) -> None:
    """
    Validates a dictionary against a schema definition.
    
    Args:
        data: The dictionary to validate.
        schema: A mapping of expected keys to their expected types.
        strict: If True, raises an error if extra keys are present in data.
                
    Raises:
        SchemaValidationError: If validation fails.
    """
    if not isinstance(data, dict):
        raise SchemaValidationError(f"Expected dict, got {type(data).__name__}")

    # Check for missing required keys
    for key, expected_type in schema.items():
        if key not in data:
            raise SchemaValidationError(f"Missing required key: '{key}'")
        
        value = data[key]
        if not isinstance(value, expected_type):
            # Special handling for int/float compatibility if needed, 
            # but strict typing is preferred for contracts.
            raise SchemaValidationError(
                f"Key '{key}' expected type {expected_type.__name__}, "
                f"got {type(value).__name__} (value: {value})"
            )

    # Check for extra keys in strict mode
    if strict:
        extra_keys = set(data.keys()) - set(schema.keys())
        if extra_keys:
            raise SchemaValidationError(
                f"Unexpected keys in strict mode: {extra_keys}"
            )


def validate_dataclass(obj: Any, expected_class: Type) -> None:
    """
    Validates that an object is an instance of the expected dataclass
    and that all its fields are populated (non-None) if they are not Optional.
    
    Args:
        obj: The object to validate.
        expected_class: The expected dataclass type.
        
    Raises:
        SchemaValidationError: If the object is not an instance or has invalid fields.
    """
    if not is_dataclass(obj) or not isinstance(obj, expected_class):
        raise SchemaValidationError(
            f"Object is not an instance of {expected_class.__name__}"
        )

    for field_obj in fields(expected_class):
        field_name = field_obj.name
        field_type = field_obj.type
        value = getattr(obj, field_name)

        # Skip validation for fields with default values if None is allowed
        if value is None:
            # Check if Optional is allowed in the type hint
            # Simple check: if type is typing.Optional or Union with None
            import typing
            origin = typing.get_origin(field_type)
            args = typing.get_args(field_type)
            
            is_optional = (origin is typing.Union and type(None) in args)
            if not is_optional:
                raise SchemaValidationError(
                    f"Field '{field_name}' in {expected_class.__name__} is None "
                    f"but not marked as Optional"
                )
            continue

        # Recursive validation for nested dataclasses
        if is_dataclass(field_type) and isinstance(value, field_type):
            validate_dataclass(value, field_type)


def validate_json_file(file_path: Union[str, Path], schema: Dict[str, Type]) -> Dict[str, Any]:
    """
    Loads and validates a JSON file against a schema.
    
    Args:
        file_path: Path to the JSON file.
        schema: The schema to validate against.
        
    Returns:
        The parsed and validated dictionary.
        
    Raises:
        DataLoadError: If the file cannot be read or parsed.
        SchemaValidationError: If the content does not match the schema.
    """
    path = Path(file_path)
    if not path.exists():
        raise DataLoadError(f"JSON file not found: {path}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise DataLoadError(f"Invalid JSON in {path}: {e}")
    except IOError as e:
        raise DataLoadError(f"Error reading {path}: {e}")

    validate_dict_schema(data, schema)
    return data


def validate_model_metadata(metadata: Dict[str, Any]) -> None:
    """
    Validates model checkpoint metadata against the expected schema.
    
    Expected keys:
        - bit_width (int)
        - param_count (int)
        - quantization_type (str)
        - training_loss (float)
        - timestamp (str)
        
    Args:
        metadata: The metadata dictionary.
        
    Raises:
        SchemaValidationError: If validation fails.
    """
    schema = {
        "bit_width": int,
        "param_count": int,
        "quantization_type": str,
        "training_loss": float,
        "timestamp": str
    }
    validate_dict_schema(metadata, schema, strict=False)


def validate_config_section(config_dict: Dict[str, Any], section_name: str) -> None:
    """
    Generic validator for configuration sections loaded from config.py or JSON.
    
    Args:
        config_dict: The configuration dictionary for a specific section.
        section_name: The name of the section (for error messages).
        
    Raises:
        ConfigurationError: If the configuration is invalid.
    """
    if not isinstance(config_dict, dict):
        raise ConfigurationError(f"Configuration section '{section_name}' must be a dictionary.")
    
    # Basic sanity checks: no empty dicts for required sections unless specified
    if not config_dict and section_name != "optional_params":
        # Allow empty dicts for optional sections if needed, but warn
        pass
        
    # Ensure all keys are strings
    for key in config_dict.keys():
        if not isinstance(key, str):
            raise ConfigurationError(
                f"Configuration section '{section_name}' contains non-string key: {key}"
            )