"""
Schema validation framework using jsonschema and pyyaml.
Provides utility functions to validate JSON/YAML data against defined schemas.
"""
import yaml
import json
from pathlib import Path
from typing import Any, Dict, List, Union, Optional
from datetime import datetime
from jsonschema import validate, ValidationError, Draft7Validator

# Import schemas defined in schemas.py
from code.tests.contract.schemas import EXECUTION_RUN_SCHEMA, REGRESSION_MODEL_SCHEMA

class SchemaValidationError(Exception):
    """Custom exception for schema validation failures."""
    pass

def load_schema_from_yaml(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a schema definition from a YAML file.

    Args:
        schema_path: Path to the YAML schema file.

    Returns:
        Dictionary containing the loaded schema.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the file contains invalid YAML.
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")

    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_type(value: Any, expected_type: str) -> bool:
    """
    Validate that a value matches a JSON Schema type definition.
    """
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    elif expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    elif expected_type == "string":
        return isinstance(value, str)
    elif expected_type == "boolean":
        return isinstance(value, bool)
    elif expected_type == "array":
        return isinstance(value, list)
    elif expected_type == "object":
        return isinstance(value, dict)
    return False

def validate_enum(value: Any, allowed_values: List[Any]) -> bool:
    """
    Validate that a value is in the list of allowed enum values.
    """
    return value in allowed_values

def validate_minimum(value: Union[int, float], minimum: Union[int, float]) -> bool:
    """
    Validate that a numeric value is >= minimum.
    """
    return value >= minimum

def validate_maximum(value: Union[int, float], maximum: Union[int, float]) -> bool:
    """
    Validate that a numeric value is <= maximum.
    """
    return value <= maximum

def validate_schema(data: Any, schema: Dict[str, Any]) -> None:
    """
    Validate data against a JSON Schema.
    Raises ValidationError if validation fails.

    Args:
        data: The data to validate.
        schema: The JSON Schema to validate against.
    """
    try:
        validate(instance=data, schema=schema, cls=Draft7Validator)
    except ValidationError as e:
        raise SchemaValidationError(f"Schema validation failed: {e.message}")

def validate_execution_run(data: Dict[str, Any]) -> None:
    """
    Validate an ExecutionRun data structure against its schema.

    Args:
        data: Dictionary containing execution run data.

    Raises:
        SchemaValidationError: If the data does not conform to the schema.
    """
    validate_schema(data, EXECUTION_RUN_SCHEMA)

def validate_regression_model(data: Dict[str, Any]) -> None:
    """
    Validate a RegressionModel data structure against its schema.

    Args:
        data: Dictionary containing regression model data.

    Raises:
        SchemaValidationError: If the data does not conform to the schema.
    """
    validate_schema(data, REGRESSION_MODEL_SCHEMA)

def validate_json_against_schema(json_data: Union[str, Dict[str, Any]], schema: Dict[str, Any]) -> bool:
    """
    Generic utility function to validate JSON data against a schema.
    This function raises ValidationError on mismatch as required by T007.

    Args:
        json_data: JSON data as a string or dictionary.
        schema: The JSON Schema to validate against.

    Returns:
        True if validation passes (only if no exception is raised).

    Raises:
        SchemaValidationError: If the data does not match the schema.
        json.JSONDecodeError: If the input string is not valid JSON.
    """
    # Parse string input if necessary
    if isinstance(json_data, str):
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError as e:
            raise SchemaValidationError(f"Invalid JSON format: {e.msg}")
    else:
        data = json_data

    # Perform validation
    try:
        validate(instance=data, schema=schema, cls=Draft7Validator)
    except ValidationError as e:
        raise SchemaValidationError(f"Validation error: {e.message} at path {'/'.join(map(str, e.path))}")

    return True
