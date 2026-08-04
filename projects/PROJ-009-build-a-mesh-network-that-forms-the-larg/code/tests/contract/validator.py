"""
Schema validation framework using PyYAML.

This module provides utilities to validate data structures against
predefined schemas for ExecutionRun and RegressionModel entities.
It ensures data integrity throughout the pipeline.
"""
import yaml
from pathlib import Path
from typing import Any, Dict, List, Union
from orchestrator.logger import get_logger

logger = get_logger(__name__)


class SchemaValidationError(Exception):
    """Exception raised when schema validation fails."""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message)
        self.details = details or {}


def load_schema_from_yaml(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a JSON Schema definition from a YAML file.
    
    Args:
        schema_path: Path to the YAML schema file
        
    Returns:
        Dictionary containing the schema definition
        
    Raises:
        SchemaValidationError: If the file cannot be loaded or parsed
    """
    try:
        path = Path(schema_path)
        if not path.exists():
            raise SchemaValidationError(
                f"Schema file not found: {schema_path}",
                {"path": str(schema_path)}
            )
        
        with open(path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
            
        if not isinstance(schema, dict):
            raise SchemaValidationError(
                "Invalid schema format: expected a dictionary",
                {"file": str(schema_path)}
            )
            
        logger.info(f"Loaded schema from {schema_path}")
        return schema
        
    except yaml.YAMLError as e:
        raise SchemaValidationError(
            f"Failed to parse YAML schema: {e}",
            {"file": str(schema_path), "error": str(e)}
        )


def validate_type(value: Any, expected_type: str) -> bool:
    """
    Validate that a value matches the expected JSON Schema type.
    
    Args:
        value: The value to validate
        expected_type: The expected type string (e.g., 'string', 'integer')
        
    Returns:
        True if the type matches, False otherwise
    """
    type_mapping = {
        'string': str,
        'integer': int,
        'number': (int, float),
        'boolean': bool,
        'array': list,
        'object': dict,
        'null': type(None)
    }
    
    if expected_type not in type_mapping:
        logger.warning(f"Unknown type: {expected_type}")
        return False
        
    expected = type_mapping[expected_type]
    
    # Special handling for integer vs number
    if expected_type == 'integer':
        return isinstance(value, int) and not isinstance(value, bool)
    elif expected_type == 'number':
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    else:
        return isinstance(value, expected)


def validate_enum(value: Any, allowed_values: List[Any]) -> bool:
    """
    Validate that a value is one of the allowed enum values.
    
    Args:
        value: The value to validate
        allowed_values: List of allowed values
        
    Returns:
        True if value is in allowed_values, False otherwise
    """
    return value in allowed_values


def validate_minimum(value: Union[int, float], minimum: Union[int, float]) -> bool:
    """Validate that a numeric value is >= minimum."""
    return value >= minimum


def validate_maximum(value: Union[int, float], maximum: Union[int, float]) -> bool:
    """Validate that a numeric value is <= maximum."""
    return value <= maximum


def validate_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate a data dictionary against a JSON Schema.
    
    Args:
        data: The data to validate
        schema: The JSON Schema to validate against
        
    Returns:
        List of error messages (empty if validation passes)
    """
    errors = []
    
    # Check required fields
    required = schema.get('required', [])
    for field in required:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    # Check property types and constraints
    properties = schema.get('properties', {})
    for field, value in data.items():
        if field not in properties:
            # Allow extra properties unless 'additionalProperties' is False
            if schema.get('additionalProperties') is False:
                errors.append(f"Unexpected field: {field}")
            continue
        
        prop_schema = properties[field]
        
        # Type validation
        if 'type' in prop_schema:
            if not validate_type(value, prop_schema['type']):
                errors.append(
                    f"Field '{field}' has invalid type. "
                    f"Expected {prop_schema['type']}, got {type(value).__name__}"
                )
                continue  # Skip further validation if type is wrong
        
        # Enum validation
        if 'enum' in prop_schema:
            if not validate_enum(value, prop_schema['enum']):
                errors.append(
                    f"Field '{field}' has invalid value '{value}'. "
                    f"Expected one of: {prop_schema['enum']}"
                )
        
        # Minimum/Maximum validation for numbers
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if 'minimum' in prop_schema:
                if not validate_minimum(value, prop_schema['minimum']):
                    errors.append(
                        f"Field '{field}' value {value} is below minimum {prop_schema['minimum']}"
                    )
            if 'maximum' in prop_schema:
                if not validate_maximum(value, prop_schema['maximum']):
                    errors.append(
                        f"Field '{field}' value {value} is above maximum {prop_schema['maximum']}"
                    )
    
    return errors


def validate_execution_run(data: Dict[str, Any]) -> bool:
    """
    Validate data against the ExecutionRun schema.
    
    Args:
        data: Dictionary containing execution run data
        
    Returns:
        True if valid, raises SchemaValidationError if invalid
    """
    from code.tests.contract.schemas import EXECUTION_RUN_SCHEMA
    
    errors = validate_schema(data, EXECUTION_RUN_SCHEMA)
    
    if errors:
        raise SchemaValidationError(
            "ExecutionRun validation failed",
            {"errors": errors, "data": data}
        )
    
    logger.debug("ExecutionRun validation passed")
    return True


def validate_regression_model(data: Dict[str, Any]) -> bool:
    """
    Validate data against the RegressionModel schema.
    
    Args:
        data: Dictionary containing regression model data
        
    Returns:
        True if valid, raises SchemaValidationError if invalid
    """
    from code.tests.contract.schemas import REGRESSION_MODEL_SCHEMA
    
    errors = validate_schema(data, REGRESSION_MODEL_SCHEMA)
    
    if errors:
        raise SchemaValidationError(
            "RegressionModel validation failed",
            {"errors": errors, "data": data}
        )
    
    logger.debug("RegressionModel validation passed")
    return True
