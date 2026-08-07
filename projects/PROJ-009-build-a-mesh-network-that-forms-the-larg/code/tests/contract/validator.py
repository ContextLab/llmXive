"""
Runtime schema validation framework for ExecutionRun and RegressionModel.
Implements validation logic using pure Python (no external jsonschema dependency)
to ensure schema compliance for data contracts.
"""
import yaml
import json
from pathlib import Path
from typing import Any, Dict, List, Union, Optional
from datetime import datetime

from orchestrator.logger import get_logger

logger = get_logger(__name__)


class SchemaValidationError(Exception):
    """Raised when a data object fails schema validation."""
    pass


def load_schema_from_yaml(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a JSON Schema from a YAML file.
    
    Args:
        schema_path: Path to the YAML schema file.
        
    Returns:
        The parsed schema dictionary.
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)
        
    if not isinstance(schema, dict):
        raise ValueError("Invalid schema format: expected a dictionary")
        
    return schema


def validate_type(value: Any, expected_type: str, field_name: str) -> None:
    """
    Validate that a value matches the expected JSON Schema type.
    
    Args:
        value: The value to check.
        expected_type: The expected type string (e.g., 'string', 'integer', 'number').
        field_name: Name of the field for error reporting.
        
    Raises:
        SchemaValidationError: If types do not match.
    """
    if expected_type == "string":
        if not isinstance(value, str):
            raise SchemaValidationError(f"Field '{field_name}' must be a string, got {type(value).__name__}")
    elif expected_type == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            raise SchemaValidationError(f"Field '{field_name}' must be an integer, got {type(value).__name__}")
    elif expected_type == "number":
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise SchemaValidationError(f"Field '{field_name}' must be a number, got {type(value).__name__}")
    elif expected_type == "boolean":
        if not isinstance(value, bool):
            raise SchemaValidationError(f"Field '{field_name}' must be a boolean, got {type(value).__name__}")
    elif expected_type == "array":
        if not isinstance(value, list):
            raise SchemaValidationError(f"Field '{field_name}' must be an array, got {type(value).__name__}")
    elif expected_type == "object":
        if not isinstance(value, dict):
            raise SchemaValidationError(f"Field '{field_name}' must be an object, got {type(value).__name__}")
    else:
        logger.warning(f"Unknown type constraint '{expected_type}' for field '{field_name}'")


def validate_enum(value: Any, allowed_values: List[Any], field_name: str) -> None:
    """
    Validate that a value is one of the allowed enum values.
    
    Args:
        value: The value to check.
        allowed_values: List of allowed values.
        field_name: Name of the field for error reporting.
        
    Raises:
        SchemaValidationError: If value is not in allowed list.
    """
    if value not in allowed_values:
        raise SchemaValidationError(
            f"Field '{field_name}' must be one of {allowed_values}, got '{value}'"
        )


def validate_minimum(value: Union[int, float], minimum: Union[int, float], field_name: str) -> None:
    """Validate value is >= minimum."""
    if value < minimum:
        raise SchemaValidationError(f"Field '{field_name}' must be >= {minimum}, got {value}")


def validate_maximum(value: Union[int, float], maximum: Union[int, float], field_name: str) -> None:
    """Validate value is <= maximum."""
    if value > maximum:
        raise SchemaValidationError(f"Field '{field_name}' must be <= {maximum}, got {value}")


def validate_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """
    Validate a data object against a JSON Schema definition.
    
    Args:
        data: The data object to validate.
        schema: The JSON Schema definition.
        
    Raises:
        SchemaValidationError: If validation fails.
    """
    if not isinstance(data, dict):
        raise SchemaValidationError("Input data must be an object/dictionary")

    properties = schema.get("properties", {})
    required = schema.get("required", [])

    # Check required fields
    for field in required:
        if field not in data:
            raise SchemaValidationError(f"Missing required field: '{field}'")

    # Validate each field present in data
    for field_name, value in data.items():
        if field_name not in properties:
            # Allow extra properties by default unless additionalProperties is false
            if schema.get("additionalProperties") is False:
                raise SchemaValidationError(f"Unexpected field: '{field_name}'")
            continue

        field_schema = properties[field_name]
        field_type = field_schema.get("type")

        if field_type:
            validate_type(value, field_type, field_name)

        # Check constraints
        if "enum" in field_schema:
            validate_enum(value, field_schema["enum"], field_name)

        if "minimum" in field_schema and isinstance(value, (int, float)):
            validate_minimum(value, field_schema["minimum"], field_name)

        if "maximum" in field_schema and isinstance(value, (int, float)):
            validate_maximum(value, field_schema["maximum"], field_name)

        # Validate date-time format if present
        if field_schema.get("format") == "date-time" and isinstance(value, str):
            try:
                datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                raise SchemaValidationError(
                    f"Field '{field_name}' must be a valid ISO 8601 datetime string"
                )

        # Validate object properties (coefficients, p_values)
        if field_type == "object" and "additionalProperties" in field_schema:
            prop_type = field_schema["additionalProperties"].get("type")
            for sub_key, sub_val in value.items():
                validate_type(sub_val, prop_type, f"{field_name}.{sub_key}")


def validate_execution_run(data: Dict[str, Any]) -> None:
    """
    Validate data against the ExecutionRun schema.
    
    Args:
        data: The execution run data.
        
    Raises:
        SchemaValidationError: If validation fails.
    """
    # Import schema from local module to avoid circular imports if necessary
    # or assume it's passed or loaded. For this implementation, we use the 
    # defined schema in the same package context.
    from code.tests.contract.schemas import EXECUTION_RUN_SCHEMA
    validate_schema(data, EXECUTION_RUN_SCHEMA)


def validate_regression_model(data: Dict[str, Any]) -> None:
    """
    Validate data against the RegressionModel schema.
    
    Args:
        data: The regression model data.
        
    Raises:
        SchemaValidationError: If validation fails.
    """
    from code.tests.contract.schemas import REGRESSION_MODEL_SCHEMA
    validate_schema(data, REGRESSION_MODEL_SCHEMA)
