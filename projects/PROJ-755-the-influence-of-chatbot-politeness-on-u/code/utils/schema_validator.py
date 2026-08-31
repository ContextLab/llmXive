"""
Schema validation utilities for the HCI Politeness project.

This module provides functions to load, validate, and verify dataset schemas
against defined contract schemas in YAML format.
"""
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import yaml
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class SchemaValidationError(Exception):
    """Raised when schema validation fails."""
    pass


def load_schema(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a schema definition from a YAML file.
    
    Args:
        schema_path: Path to the schema YAML file.
        
    Returns:
        Dictionary containing the schema definition.
        
    Raises:
        FileNotFoundError: If the schema file doesn't exist.
        yaml.YAMLError: If the YAML is malformed.
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
        
    with open(path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)
        
    if not isinstance(schema, dict):
        raise SchemaValidationError("Schema must be a YAML dictionary")
        
    return schema


def validate_type(value: Any, expected_type: str) -> bool:
    """
    Validate that a value matches the expected type.
    
    Args:
        value: The value to check.
        expected_type: The expected type as a string (e.g., 'string', 'integer', 'number', 'boolean', 'array', 'object').
        
    Returns:
        True if the value matches the type, False otherwise.
    """
    type_mapping = {
        'string': str,
        'integer': int,
        'number': (int, float),
        'boolean': bool,
        'array': (list, tuple),
        'object': dict
    }
    
    if expected_type not in type_mapping:
        logger.warning(f"Unknown type: {expected_type}")
        return True
        
    expected = type_mapping[expected_type]
    
    # Special handling for boolean (since bool is subclass of int in Python)
    if expected_type == 'boolean':
        return isinstance(value, bool)
    if expected_type == 'integer':
        return isinstance(value, int) and not isinstance(value, bool)
        
    return isinstance(value, expected)


def validate_value_constraints(value: Any, constraints: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate that a value meets specified constraints.
    
    Args:
        value: The value to check.
        constraints: Dictionary of constraints (e.g., {'min': 0, 'max': 100, 'pattern': '^[A-Z]+$'}).
        
    Returns:
        Tuple of (is_valid, error_message).
    """
    if 'min' in constraints and value < constraints['min']:
        return False, f"Value {value} is less than minimum {constraints['min']}"
        
    if 'max' in constraints and value > constraints['max']:
        return False, f"Value {value} is greater than maximum {constraints['max']}"
        
    if 'pattern' in constraints and isinstance(value, str):
        if not re.match(constraints['pattern'], value):
            return False, f"Value '{value}' does not match pattern '{constraints['pattern']}'"
            
    if 'enum' in constraints and value not in constraints['enum']:
        return False, f"Value '{value}' not in allowed values {constraints['enum']}"
        
    if 'min_length' in constraints and isinstance(value, str):
        if len(value) < constraints['min_length']:
            return False, f"String length {len(value)} is less than minimum {constraints['min_length']}"
            
    if 'max_length' in constraints and isinstance(value, str):
        if len(value) > constraints['max_length']:
            return False, f"String length {len(value)} is greater than maximum {constraints['max_length']}"
            
    return True, ""


def validate_property(value: Any, property_def: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate a single property against its definition.
    
    Args:
        value: The value to validate.
        property_def: The property definition from the schema.
        
    Returns:
        Tuple of (is_valid, error_message).
    """
    # Check type
    if 'type' in property_def:
        if not validate_type(value, property_def['type']):
            return False, f"Type mismatch: expected {property_def['type']}, got {type(value).__name__}"
            
    # Check constraints
    if 'constraints' in property_def:
        is_valid, error = validate_value_constraints(value, property_def['constraints'])
        if not is_valid:
            return False, error
            
    return True, ""


def validate_object(obj: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate an object against a schema definition.
    
    Args:
        obj: The object to validate.
        schema: The schema definition for the object.
        
    Returns:
        List of validation errors (empty if valid).
    """
    errors = []
    
    properties = schema.get('properties', {})
    required = schema.get('required', [])
    
    # Check required fields
    for field in required:
        if field not in obj:
            errors.append(f"Missing required field: {field}")
            
    # Validate each property
    for prop_name, prop_value in obj.items():
        if prop_name in properties:
            is_valid, error = validate_property(prop_value, properties[prop_name])
            if not is_valid:
                errors.append(f"Invalid value for '{prop_name}': {error}")
        elif prop_name not in schema.get('additionalProperties', True):
            errors.append(f"Unexpected field: {prop_name}")
            
    return errors


def validate_dataset_schema(schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate the schema definition itself for completeness.
    
    Args:
        schema: The schema definition to validate.
        
    Returns:
        Tuple of (is_valid, list of errors).
    """
    errors = []
    
    # Check for required schema keys
    if 'entity' not in schema:
        errors.append("Schema missing 'entity' key")
        
    if 'properties' not in schema:
        errors.append("Schema missing 'properties' key")
        
    # Validate each property definition
    for prop_name, prop_def in schema.get('properties', {}).items():
        if 'type' not in prop_def:
            errors.append(f"Property '{prop_name}' missing 'type' definition")
            
    return len(errors) == 0, errors


def validate_dataset(df: pd.DataFrame, schema_path: Union[str, Path]) -> Tuple[bool, List[str]]:
    """
    Validate a pandas DataFrame against a schema definition.
    
    Args:
        df: The DataFrame to validate.
        schema_path: Path to the schema YAML file.
        
    Returns:
        Tuple of (is_valid, list of errors).
    """
    schema = load_schema(schema_path)
    
    # Validate schema itself first
    is_valid, schema_errors = validate_dataset_schema(schema)
    if not is_valid:
        return False, [f"Schema error: {e}" for e in schema_errors]
        
    errors = []
    properties = schema.get('properties', {})
    required = schema.get('required', [])
    
    # Check for required columns
    for field in required:
        if field not in df.columns:
            errors.append(f"Missing required column: {field}")
            
    # Validate each column
    for col_name in df.columns:
        if col_name in properties:
            prop_def = properties[col_name]
            
            # Check type mapping
            type_mapping = {
                'string': 'object',
                'integer': 'int64',
                'number': 'float64',
                'boolean': 'bool',
                'array': 'object',
                'object': 'object'
            }
            
            expected_type = type_mapping.get(prop_def.get('type', 'string'))
            actual_type = str(df[col_name].dtype)
            
            # For now, do a basic type check
            if prop_def.get('type') == 'integer' and not pd.api.types.is_integer_dtype(df[col_name]):
                errors.append(f"Column '{col_name}' should be integer, got {actual_type}")
            elif prop_def.get('type') == 'number' and not pd.api.types.is_numeric_dtype(df[col_name]):
                errors.append(f"Column '{col_name}' should be numeric, got {actual_type}")
            elif prop_def.get('type') == 'boolean' and not pd.api.types.is_bool_dtype(df[col_name]):
                errors.append(f"Column '{col_name}' should be boolean, got {actual_type}")
                
            # Check for null values in required fields
            if col_name in required and df[col_name].isna().any():
                errors.append(f"Column '{col_name}' contains null values but is required")
                
            # Check constraints
            if 'constraints' in prop_def:
                constraints = prop_def['constraints']
                
                if 'min' in constraints and pd.api.types.is_numeric_dtype(df[col_name]):
                    min_val = df[col_name].min()
                    if min_val < constraints['min']:
                        errors.append(f"Column '{col_name}' has values below minimum {constraints['min']} (min found: {min_val})")
                        
                if 'max' in constraints and pd.api.types.is_numeric_dtype(df[col_name]):
                    max_val = df[col_name].max()
                    if max_val > constraints['max']:
                        errors.append(f"Column '{col_name}' has values above maximum {constraints['max']} (max found: {max_val})")
                        
                if 'enum' in constraints:
                    unique_values = df[col_name].unique()
                    invalid_values = [v for v in unique_values if pd.notna(v) and v not in constraints['enum']]
                    if invalid_values:
                        errors.append(f"Column '{col_name}' contains invalid values: {invalid_values[:5]}...")
                        
    return len(errors) == 0, errors


def get_missing_fields(df: pd.DataFrame, schema_path: Union[str, Path]) -> List[str]:
    """
    Get a list of fields that are missing from the DataFrame but required by the schema.
    
    Args:
        df: The DataFrame to check.
        schema_path: Path to the schema YAML file.
        
    Returns:
        List of missing required field names.
    """
    schema = load_schema(schema_path)
    required = schema.get('required', [])
    
    missing = []
    for field in required:
        if field not in df.columns:
            missing.append(field)
            
    return missing


def validate_dataset_schema_wrapper(schema_path: Union[str, Path]) -> Tuple[bool, List[str]]:
    """
    Wrapper function to validate a schema file against itself.
    
    Args:
        schema_path: Path to the schema YAML file.
        
    Returns:
        Tuple of (is_valid, list of errors).
    """
    schema = load_schema(schema_path)
    return validate_dataset_schema(schema)