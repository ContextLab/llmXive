"""
Schema validation helpers for YAML/JSON configuration and data files.
Provides strict type checking, required field validation, range constraints,
and full schema validation against defined schemas.
"""
import json
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable
from collections.abc import Mapping


class ValidationError(Exception):
    """Custom exception for validation errors."""
    def __init__(self, message: str, path: Optional[str] = None, details: Optional[Dict] = None):
        super().__init__(message)
        self.path = path
        self.details = details or {}

def load_yaml(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load and parse a YAML file.

    Args:
        file_path: Path to the YAML file.

    Returns:
        Parsed YAML content as a dictionary.

    Raises:
        ValidationError: If file cannot be read or parsed.
    """
    path = Path(file_path)
    if not path.exists():
        raise ValidationError(f"YAML file not found: {path}", path=str(path))

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if data is None:
                return {}
            if not isinstance(data, Mapping):
                raise ValidationError(f"YAML file must contain a mapping, got {type(data).__name__}", path=str(path))
            return dict(data)
    except yaml.YAMLError as e:
        raise ValidationError(f"Failed to parse YAML: {e}", path=str(path))
    except Exception as e:
        raise ValidationError(f"Failed to read YAML file: {e}", path=str(path))

def load_json(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load and parse a JSON file.

    Args:
        file_path: Path to the JSON file.

    Returns:
        Parsed JSON content as a dictionary.

    Raises:
        ValidationError: If file cannot be read or parsed.
    """
    path = Path(file_path)
    if not path.exists():
        raise ValidationError(f"JSON file not found: {path}", path=str(path))

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, Mapping):
                raise ValidationError(f"JSON file must contain a mapping, got {type(data).__name__}", path=str(path))
            return dict(data)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Failed to parse JSON: {e}", path=str(path))
    except Exception as e:
        raise ValidationError(f"Failed to read JSON file: {e}", path=str(path))

def validate_type(value: Any, expected_type: type, field_name: str) -> None:
    """
    Validate that a value matches the expected type.

    Args:
        value: The value to check.
        expected_type: The expected Python type.
        field_name: Name of the field for error reporting.

    Raises:
        ValidationError: If type does not match.
    """
    if not isinstance(value, expected_type):
        raise ValidationError(
            f"Field '{field_name}' must be of type {expected_type.__name__}, got {type(value).__name__}",
            details={"field": field_name, "expected": expected_type.__name__, "got": type(value).__name__}
        )

def validate_required_fields(data: Dict[str, Any], required_fields: List[str], context: str = "Configuration") -> None:
    """
    Validate that all required fields are present in a dictionary.

    Args:
        data: The dictionary to check.
        required_fields: List of required field names.
        context: Context description for error messages.

    Raises:
        ValidationError: If any required field is missing.
    """
    missing = [field for field in required_fields if field not in data]
    if missing:
        raise ValidationError(
            f"Missing required fields in {context}: {', '.join(missing)}",
            details={"missing_fields": missing, "context": context}
        )

def validate_range(value: Union[int, float], min_val: Optional[float] = None, max_val: Optional[float] = None, field_name: str = "value") -> None:
    """
    Validate that a numeric value is within specified bounds.

    Args:
        value: The numeric value to check.
        min_val: Minimum allowed value (inclusive).
        max_val: Maximum allowed value (inclusive).
        field_name: Name of the field for error reporting.

    Raises:
        ValidationError: If value is outside bounds.
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(
            f"Field '{field_name}' must be numeric for range validation",
            details={"field": field_name, "value": value}
        )

    if min_val is not None and value < min_val:
        raise ValidationError(
            f"Field '{field_name}' value {value} is below minimum {min_val}",
            details={"field": field_name, "value": value, "min": min_val}
        )

    if max_val is not None and value > max_val:
        raise ValidationError(
            f"Field '{field_name}' value {value} is above maximum {max_val}",
            details={"field": field_name, "value": value, "max": max_val}
        )

def validate_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """
    Validate a dictionary against a schema definition.

    Schema format:
    {
        "field_name": {
            "type": <type>,
            "required": <bool>,
            "min": <float>,
            "max": <float>,
            "allowed_values": [<list>]
        }
    }

    Args:
        data: The dictionary to validate.
        schema: The schema definition.

    Raises:
        ValidationError: If validation fails.
    """
    for field_name, rules in schema.items():
        is_required = rules.get("required", False)

        if field_name not in data:
            if is_required:
                raise ValidationError(
                    f"Required field '{field_name}' is missing",
                    details={"field": field_name, "required": True}
                )
            continue

        value = data[field_name]

        # Type check
        if "type" in rules:
            validate_type(value, rules["type"], field_name)

        # Range check
        if "min" in rules or "max" in rules:
            validate_range(value, rules.get("min"), rules.get("max"), field_name)

        # Allowed values check
        if "allowed_values" in rules:
            if value not in rules["allowed_values"]:
                raise ValidationError(
                    f"Field '{field_name}' value '{value}' not in allowed values: {rules['allowed_values']}",
                    details={"field": field_name, "value": value, "allowed": rules["allowed_values"]}
                )

def validate_config_file(config_path: Union[str, Path], schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load and validate a configuration file against a schema.

    Args:
        config_path: Path to the config file (YAML or JSON).
        schema: The schema definition to validate against.

    Returns:
        The validated configuration dictionary.

    Raises:
        ValidationError: If loading or validation fails.
    """
    path = Path(config_path)

    # Determine file type and load
    if path.suffix.lower() in ['.yaml', '.yml']:
        data = load_yaml(path)
    elif path.suffix.lower() == '.json':
        data = load_json(path)
    else:
        raise ValidationError(
            f"Unsupported config file format: {path.suffix}",
            path=str(path)
        )

    # Validate against schema
    validate_schema(data, schema)

    return data
