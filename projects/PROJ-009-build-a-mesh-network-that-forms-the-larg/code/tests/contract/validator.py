"""
Schema validation framework using PyYAML.
Validates data structures against defined schemas for ExecutionRun and RegressionModel.
"""
import yaml
from pathlib import Path
from typing import Any, Dict, List, Union
from orchestrator.logger import get_logger

logger = get_logger(__name__)

class SchemaValidationError(Exception):
    """Raised when data fails schema validation."""
    pass

def load_schema_from_yaml(schema_path: Path) -> Dict[str, Any]:
    """
    Load a schema definition from a YAML file.
    
    Args:
        schema_path: Path to the YAML schema file
        
    Returns:
        Dictionary containing the schema definition
        
    Raises:
        FileNotFoundError: If schema file doesn't exist
        yaml.YAMLError: If YAML parsing fails
    """
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_type(value: Any, expected_type: str, field_path: str) -> None:
    """
    Validate that a value matches the expected type.
    
    Args:
        value: The value to validate
        expected_type: Expected type string ('string', 'integer', 'number', 'boolean', 'array', 'object')
        field_path: Dot-notation path to the field for error reporting
        
    Raises:
        SchemaValidationError: If type mismatch occurs
    """
    type_map = {
        'string': str,
        'integer': int,
        'number': (int, float),
        'boolean': bool,
        'array': list,
        'object': dict
    }
    
    if expected_type not in type_map:
        raise SchemaValidationError(f"Unknown type '{expected_type}' at {field_path}")
    
    expected_python_type = type_map[expected_type]
    
    # Special handling for integer vs number (int is also a number in Python)
    if expected_type == 'integer' and isinstance(value, bool):
        # In Python, bool is a subclass of int, but we don't want to accept booleans as integers
        raise SchemaValidationError(f"Expected integer at {field_path}, got boolean")
        
    if expected_type == 'number' and isinstance(value, bool):
        raise SchemaValidationError(f"Expected number at {field_path}, got boolean")
        
    if not isinstance(value, expected_python_type):
        raise SchemaValidationError(
            f"Type mismatch at {field_path}: expected {expected_type}, got {type(value).__name__}"
        )

def validate_enum(value: Any, allowed_values: List[Any], field_path: str) -> None:
    """Validate that a value is in the allowed enum list."""
    if value not in allowed_values:
        raise SchemaValidationError(
            f"Invalid value at {field_path}: '{value}' not in {allowed_values}"
        )

def validate_minimum(value: Union[int, float], min_val: Union[int, float], field_path: str) -> None:
    """Validate that a numeric value meets minimum requirement."""
    if value < min_val:
        raise SchemaValidationError(
            f"Value at {field_path} ({value}) is less than minimum ({min_val})"
        )

def validate_maximum(value: Union[int, float], max_val: Union[int, float], field_path: str) -> None:
    """Validate that a numeric value meets maximum requirement."""
    if value > max_val:
        raise SchemaValidationError(
            f"Value at {field_path} ({value}) exceeds maximum ({max_val})"
        )

def validate_schema(data: Dict[str, Any], schema: Dict[str, Any], schema_name: str = "Unknown") -> bool:
    """
    Validate a data dictionary against a schema definition.
    
    Args:
        data: The data dictionary to validate
        schema: The schema definition (loaded from YAML or defined in code)
        schema_name: Name of the schema for error reporting
        
    Returns:
        True if validation passes
        
    Raises:
        SchemaValidationError: If validation fails
    """
    if not isinstance(data, dict):
        raise SchemaValidationError(f"Expected object for {schema_name}, got {type(data).__name__}")
    
    # Check required fields
    if 'required' in schema:
        for required_field in schema['required']:
            if required_field not in data:
                raise SchemaValidationError(
                    f"Missing required field '{required_field}' in {schema_name}"
                )
    
    # Validate properties
    if 'properties' in schema:
        for prop_name, prop_schema in schema['properties'].items():
            if prop_name not in data:
                continue  # Optional field, skip if not present
            
            value = data[prop_name]
            field_path = f"{schema_name}.{prop_name}"
            
            # Type validation
            if 'type' in prop_schema:
                validate_type(value, prop_schema['type'], field_path)
            
            # Enum validation
            if 'enum' in prop_schema:
                validate_enum(value, prop_schema['enum'], field_path)
            
            # Min/Max validation for numbers
            if 'minimum' in prop_schema and isinstance(value, (int, float)):
                validate_minimum(value, prop_schema['minimum'], field_path)
            
            if 'maximum' in prop_schema and isinstance(value, (int, float)):
                validate_maximum(value, prop_schema['maximum'], field_path)
            
            # Nested object validation
            if prop_schema['type'] == 'object' and 'properties' in prop_schema:
                if isinstance(value, dict):
                    validate_schema(value, prop_schema, field_path)
            
            # Array validation
            if prop_schema['type'] == 'array' and 'items' in prop_schema:
                if isinstance(value, list):
                    item_schema = prop_schema['items']
                    for idx, item in enumerate(value):
                        item_path = f"{field_path}[{idx}]"
                        if 'type' in item_schema:
                            validate_type(item, item_schema['type'], item_path)
    
    # Check for additional properties if not allowed
    if schema.get('additionalProperties') is False:
        allowed_keys = set(schema.get('properties', {}).keys())
        for key in data.keys():
            if key not in allowed_keys:
                raise SchemaValidationError(
                    f"Unexpected property '{key}' in {schema_name} (additionalProperties: false)"
                )
    
    logger.debug(f"Validation passed for {schema_name}")
    return True

def validate_execution_run(data: Dict[str, Any]) -> bool:
    """
    Validate an ExecutionRun data structure.
    
    Args:
        data: Dictionary containing execution run data
        
    Returns:
        True if valid
        
    Raises:
        SchemaValidationError: If validation fails
    """
    from .schemas import EXECUTION_RUN_SCHEMA
    return validate_schema(data, EXECUTION_RUN_SCHEMA, "ExecutionRun")

def validate_regression_model(data: Dict[str, Any]) -> bool:
    """
    Validate a RegressionModel data structure.
    
    Args:
        data: Dictionary containing regression model data
        
    Returns:
        True if valid
        
    Raises:
        SchemaValidationError: If validation fails
    """
    from .schemas import REGRESSION_MODEL_SCHEMA
    return validate_schema(data, REGRESSION_MODEL_SCHEMA, "RegressionModel")
