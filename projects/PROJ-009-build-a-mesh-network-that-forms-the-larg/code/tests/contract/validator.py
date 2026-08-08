"""
Schema validation utility for ExecutionRun and RegressionModel structures.
Uses jsonschema for validation against YAML-defined schemas.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import jsonschema
from jsonschema import ValidationError, Draft7Validator
import yaml

from orchestrator.logger import get_logger

logger = get_logger(__name__)

# Path to the schemas directory relative to project root
SCHEMAS_DIR = Path(__file__).parent / "schemas"

class SchemaValidationError(Exception):
    """Custom exception for schema validation failures."""
    pass

def load_schema_from_yaml(schema_file: Path) -> Dict[str, Any]:
    """
    Load a JSON schema defined in a YAML file.
    
    Args:
        schema_file: Path to the YAML schema file.
        
    Returns:
        The schema as a dictionary.
        
    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the YAML is invalid.
    """
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")
    
    with open(schema_file, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)
    
    return schema

def validate_json_against_schema(
    data: Union[Dict[str, Any], str],
    schema: Union[Dict[str, Any], str, Path],
    schema_name: str = "Unknown"
) -> None:
    """
    Validate a JSON object (or JSON string) against a schema.
    
    This is the core utility function requested in T007.
    It raises a SchemaValidationError (wrapping jsonschema.ValidationError)
    if the data does not conform to the schema.
    
    Args:
        data: The data to validate (dict or JSON string).
        schema: The schema to validate against (dict, JSON string, or Path to YAML).
        schema_name: Human-readable name for error messages.
        
    Raises:
        SchemaValidationError: If validation fails.
        TypeError: If data format is incorrect.
    """
    # Load schema if path provided
    if isinstance(schema, Path):
        try:
            schema_dict = load_schema_from_yaml(schema)
        except Exception as e:
            logger.error(f"Failed to load schema {schema_name}: {e}")
            raise
    elif isinstance(schema, str):
        # Assume it's a JSON string if it starts with '{'
        if schema.strip().startswith('{'):
            try:
                schema_dict = json.loads(schema)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON schema string: {e}")
        else:
            # Assume it's a file path string
            schema_dict = load_schema_from_yaml(Path(schema))
    else:
        schema_dict = schema

    # Parse data if it's a JSON string
    if isinstance(data, str):
        try:
            data_dict = json.loads(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON data string: {e}")
    else:
        data_dict = data

    # Validate
    try:
        validator = Draft7Validator(schema_dict)
        errors = list(validator.iter_errors(data_dict))
        if errors:
            error_msgs = [f" - {e.message} (path: {list(e.path)})" for e in errors]
            full_msg = f"Schema validation failed for {schema_name}:\n" + "\n".join(error_msgs)
            logger.error(full_msg)
            raise SchemaValidationError(full_msg)
        
        logger.debug(f"Schema validation passed for {schema_name}")
        
    except SchemaValidationError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during validation of {schema_name}: {e}")
        raise

def validate_execution_run(data: Union[Dict[str, Any], str]) -> None:
    """
    Validate data against the ExecutionRun schema.
    
    Args:
        data: The data to validate.
        
    Raises:
        SchemaValidationError: If validation fails.
    """
    schema_path = SCHEMAS_DIR / "execution_run.yaml"
    validate_json_against_schema(data, schema_path, "ExecutionRun")

def validate_regression_model(data: Union[Dict[str, Any], str]) -> None:
    """
    Validate a RegressionModel data structure against its schema.

    Args:
        data: The data to validate.
        
    Raises:
        SchemaValidationError: If the data does not conform to the schema.
    """
    schema_path = SCHEMAS_DIR / "regression_model.yaml"
    validate_json_against_schema(data, schema_path, "RegressionModel")

def get_execution_run_schema() -> Dict[str, Any]:
    """Load and return the ExecutionRun schema dictionary."""
    return load_schema_from_yaml(SCHEMAS_DIR / "execution_run.yaml")

def get_regression_model_schema() -> Dict[str, Any]:
    """Load and return the RegressionModel schema dictionary."""
    return load_schema_from_yaml(SCHEMAS_DIR / "regression_model.yaml")
