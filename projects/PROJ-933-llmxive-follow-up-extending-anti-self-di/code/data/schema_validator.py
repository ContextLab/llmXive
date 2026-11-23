"""
Schema validation logic for llmXive pipeline data artifacts.

This module provides functions to validate JSON/YAML data against
predefined schema definitions to ensure data integrity and compliance
with project contracts.
"""
import json
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
import re


class SchemaValidationError(Exception):
    """Raised when data does not conform to the expected schema."""
    pass


def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load a schema definition from a YAML or JSON file.
    
    Args:
        schema_path: Path to the schema file (supports .yaml, .yml, .json)
        
    Returns:
        Dictionary containing the schema definition
        
    Raises:
        FileNotFoundError: If schema file does not exist
        ValueError: If file format is unsupported or parsing fails
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
    with open(path, 'r', encoding='utf-8') as f:
        if path.suffix in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        elif path.suffix == '.json':
            return json.load(f)
        else:
            raise ValueError(f"Unsupported schema format: {path.suffix}")


def validate_type(value: Any, expected_type: str) -> bool:
    """
    Check if a value matches the expected type.
    
    Supported types: string, number, integer, boolean, array, object, null
    
    Args:
        value: The value to check
        expected_type: The expected type string
        
    Returns:
        True if the value matches the type, False otherwise
    """
    type_map = {
        'string': str,
        'number': (int, float),
        'integer': int,
        'boolean': bool,
        'array': list,
        'object': dict,
        'null': type(None)
    }
    
    if expected_type not in type_map:
        raise ValueError(f"Unknown type: {expected_type}")
        
    expected = type_map[expected_type]
    
    # Special case: in Python, bool is a subclass of int
    if expected_type == 'integer' and isinstance(value, bool):
        return False
    if expected_type == 'boolean' and isinstance(value, int) and not isinstance(value, bool):
        return False
        
    return isinstance(value, expected)


def validate_value(value: Any, schema: Dict[str, Any]) -> None:
    """
    Validate a value against a schema definition.
    
    Args:
        value: The value to validate
        schema: The schema definition for this value
        
    Raises:
        SchemaValidationError: If validation fails
    """
    if 'type' in schema:
        if not validate_type(value, schema['type']):
            raise SchemaValidationError(
                f"Expected type '{schema['type']}', got {type(value).__name__}"
            )
    
    # String constraints
    if schema.get('type') == 'string' and isinstance(value, str):
        if 'minLength' in schema and len(value) < schema['minLength']:
            raise SchemaValidationError(
                f"String length {len(value)} is less than minimum {schema['minLength']}"
            )
        if 'maxLength' in schema and len(value) > schema['maxLength']:
            raise SchemaValidationError(
                f"String length {len(value)} exceeds maximum {schema['maxLength']}"
            )
        if 'pattern' in schema:
            if not re.match(schema['pattern'], value):
                raise SchemaValidationError(
                    f"String '{value}' does not match pattern '{schema['pattern']}'"
                )
        if 'enum' in schema and value not in schema['enum']:
            raise SchemaValidationError(
                f"Value '{value}' not in allowed values: {schema['enum']}"
            )
    
    # Number constraints
    if schema.get('type') in ['number', 'integer'] and isinstance(value, (int, float)) and not isinstance(value, bool):
        if 'minimum' in schema and value < schema['minimum']:
            raise SchemaValidationError(
                f"Value {value} is less than minimum {schema['minimum']}"
            )
        if 'maximum' in schema and value > schema['maximum']:
            raise SchemaValidationError(
                f"Value {value} exceeds maximum {schema['maximum']}"
            )
        if 'exclusiveMinimum' in schema and value <= schema['exclusiveMinimum']:
            raise SchemaValidationError(
                f"Value {value} is not greater than {schema['exclusiveMinimum']}"
            )
        if 'exclusiveMaximum' in schema and value >= schema['exclusiveMaximum']:
            raise SchemaValidationError(
                f"Value {value} is not less than {schema['exclusiveMaximum']}"
            )
    
    # Array constraints
    if schema.get('type') == 'array' and isinstance(value, list):
        if 'minItems' in schema and len(value) < schema['minItems']:
            raise SchemaValidationError(
                f"Array length {len(value)} is less than minimum {schema['minItems']}"
            )
        if 'maxItems' in schema and len(value) > schema['maxItems']:
            raise SchemaValidationError(
                f"Array length {len(value)} exceeds maximum {schema['maxItems']}"
            )
        if 'items' in schema:
            for i, item in enumerate(value):
                try:
                    validate_value(item, schema['items'])
                except SchemaValidationError as e:
                    raise SchemaValidationError(f"Item at index {i}: {e}")


def validate_object(obj: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """
    Validate an object (dictionary) against a schema definition.
    
    Args:
        obj: The object to validate
        schema: The schema definition for this object
        
    Raises:
        SchemaValidationError: If validation fails
    """
    if schema.get('type') == 'object' and not isinstance(obj, dict):
        raise SchemaValidationError(f"Expected object, got {type(obj).__name__}")
    
    # Required fields
    if 'required' in schema:
        for field in schema['required']:
            if field not in obj:
                raise SchemaValidationError(f"Missing required field: {field}")
    
    # Property validation
    properties = schema.get('properties', {})
    additional_properties = schema.get('additionalProperties', True)
    
    for key, value in obj.items():
        if key in properties:
            try:
                validate_value(value, properties[key])
            except SchemaValidationError as e:
                raise SchemaValidationError(f"Field '{key}': {e}")
        elif additional_properties is False:
            raise SchemaValidationError(f"Additional property not allowed: {key}")
        elif isinstance(additional_properties, dict):
            try:
                validate_value(value, additional_properties)
            except SchemaValidationError as e:
                raise SchemaValidationError(f"Additional property '{key}': {e}")


def validate_json_against_schema(data: Any, schema: Dict[str, Any]) -> None:
    """
    Validate JSON data against a schema.
    
    Args:
        data: The data to validate
        schema: The schema definition
        
    Raises:
        SchemaValidationError: If validation fails
    """
    validate_value(data, schema)


def validate_dataset_schema(data_path: str, schema_path: str) -> bool:
    """
    Validate a dataset JSON file against its schema.
    
    Args:
        data_path: Path to the dataset JSON file
        schema_path: Path to the schema file
        
    Returns:
        True if validation passes
        
    Raises:
        SchemaValidationError: If validation fails
        FileNotFoundError: If data or schema file not found
    """
    data = load_json_file(data_path)
    schema = load_schema(schema_path)
    validate_json_against_schema(data, schema)
    return True


def validate_training_output_schema(data_path: str, schema_path: str) -> bool:
    """
    Validate a training output JSON file against its schema.
    
    Args:
        data_path: Path to the training output JSON file
        schema_path: Path to the schema file
        
    Returns:
        True if validation passes
        
    Raises:
        SchemaValidationError: If validation fails
        FileNotFoundError: If data or schema file not found
    """
    data = load_json_file(data_path)
    schema = load_schema(schema_path)
    validate_json_against_schema(data, schema)
    return True


def validate_analysis_results_schema(data_path: str, schema_path: str) -> bool:
    """
    Validate an analysis results JSON file against its schema.
    
    Args:
        data_path: Path to the analysis results JSON file
        schema_path: Path to the schema file
        
    Returns:
        True if validation passes
        
    Raises:
        SchemaValidationError: If validation fails
        FileNotFoundError: If data or schema file not found
    """
    data = load_json_file(data_path)
    schema = load_schema(schema_path)
    validate_json_against_schema(data, schema)
    return True


def load_json_file(file_path: str) -> Any:
    """
    Load and parse a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Parsed JSON data
        
    Raises:
        FileNotFoundError: If file not found
        json.JSONDecodeError: If JSON parsing fails
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")
        
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_file_exists(file_path: str) -> bool:
    """
    Check if a file exists.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if file exists
    """
    return Path(file_path).exists()


def validate_directory_exists(dir_path: str) -> bool:
    """
    Check if a directory exists.
    
    Args:
        dir_path: Path to the directory
        
    Returns:
        True if directory exists
    """
    path = Path(dir_path)
    return path.exists() and path.is_dir()
