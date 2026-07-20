"""
Data validation utilities for the social feedback pipeline.

This module loads the interaction schema and provides validation functions
to ensure data integrity before processing.
"""
import json
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, ValidationError, create_model
import pandas as pd
import numpy as np

from .config import CONTRACTS_DIR, logger


def load_schema(schema_name: str = "interaction_schema") -> Dict[str, Any]:
    """
    Load a JSON/YAML schema from the contracts directory.
    
    Args:
        schema_name: Name of the schema file (without extension)
        
    Returns:
        The loaded schema as a dictionary
        
    Raises:
        FileNotFoundError: If the schema file does not exist
        yaml.YAMLError: If the schema is malformed
    """
    schema_path = CONTRACTS_DIR / f"{schema_name}.schema.yaml"
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def _get_required_fields(schema: Dict[str, Any]) -> Set[str]:
    """Extract required field names from the schema."""
    properties = schema.get('properties', {})
    required = set(schema.get('required', []))
    
    # If 'required' is not explicitly defined, assume all properties are required
    # unless the schema uses 'allOf' or other complex constructs
    if not required and properties:
        return set(properties.keys())
    
    return required


def _get_field_types(schema: Dict[str, Any]) -> Dict[str, str]:
    """Extract expected types for each field from the schema."""
    properties = schema.get('properties', {})
    types = {}
    
    for field_name, field_def in properties.items():
        if 'type' in field_def:
            types[field_name] = field_def['type']
        elif 'items' in field_def:
            # Array type - store as 'array'
            types[field_name] = 'array'
        else:
            # Default to string if type is not specified
            types[field_name] = 'string'
            
    return types


def _map_pandas_dtype_to_schema(pandas_dtype: str, schema_type: str) -> bool:
    """
    Check if a pandas dtype is compatible with a schema type.
    
    Args:
        pandas_dtype: The dtype string from pandas (e.g., 'object', 'int64')
        schema_type: The expected type from the schema (e.g., 'string', 'integer')
        
    Returns:
        True if compatible, False otherwise
    """
    compatibility_map = {
        'string': ['object', 'string'],
        'integer': ['int8', 'int16', 'int32', 'int64', 'uint8', 'uint16', 'uint32', 'uint64'],
        'number': ['float16', 'float32', 'float64', 'int8', 'int16', 'int32', 'int64', 
                  'uint8', 'uint16', 'uint32', 'uint64'],
        'boolean': ['bool'],
        'array': ['object'],  # Arrays are typically stored as objects/lists in pandas
    }
    
    compatible_dtypes = compatibility_map.get(schema_type, [])
    return pandas_dtype in compatible_dtypes


def validate_dataframe(df: pd.DataFrame, schema_name: str = "interaction_schema") -> None:
    """
    Validate a DataFrame against a JSON schema.
    
    This function checks:
    1. All required fields are present
    2. Field types match the schema expectations
    3. No null values exist in required fields
    
    Args:
        df: The pandas DataFrame to validate
        schema_name: Name of the schema to validate against
        
    Raises:
        ValueError: If validation fails, with a detailed error message
    """
    try:
        schema = load_schema(schema_name)
    except FileNotFoundError as e:
        logger.error(f"Failed to load schema: {e}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse schema: {e}")
        raise
    
    required_fields = _get_required_fields(schema)
    field_types = _get_field_types(schema)
    
    errors: List[str] = []
    
    # Check 1: Required fields exist
    df_columns = set(df.columns)
    missing_fields = required_fields - df_columns
    
    if missing_fields:
        errors.append(f"Missing required columns: {sorted(missing_fields)}")
    
    # Check 2: Type validation for existing columns
    for col in df.columns:
        if col in field_types:
            expected_type = field_types[col]
            actual_dtype = str(df[col].dtype)
            
            if not _map_pandas_dtype_to_schema(actual_dtype, expected_type):
                errors.append(
                    f"Column '{col}' has dtype '{actual_dtype}' but expected '{expected_type}'"
                )
    
    # Check 3: Null values in required fields
    for field in required_fields:
        if field in df.columns:
            null_count = df[field].isna().sum()
            if null_count > 0:
                errors.append(
                    f"Column '{field}' contains {null_count} null values "
                    f"(required field cannot have nulls)"
                )
    
    # If there are errors, raise a comprehensive exception
    if errors:
        error_msg = "Data validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"DataFrame validation successful against schema '{schema_name}'")


def validate_row(row: Dict[str, Any], schema_name: str = "interaction_schema") -> bool:
    """
    Validate a single row (dictionary) against the schema.
    
    Args:
        row: Dictionary representing a single row
        schema_name: Name of the schema to validate against
        
    Returns:
        True if valid, False otherwise
        
    Raises:
        ValueError: If validation fails
    """
    try:
        schema = load_schema(schema_name)
    except (FileNotFoundError, yaml.YAMLError) as e:
        logger.error(f"Failed to load schema for row validation: {e}")
        raise
    
    required_fields = _get_required_fields(schema)
    field_types = _get_field_types(schema)
    
    errors: List[str] = []
    
    # Check required fields
    missing_fields = required_fields - set(row.keys())
    if missing_fields:
        errors.append(f"Missing required fields: {sorted(missing_fields)}")
    
    # Check types
    for field, value in row.items():
        if field in field_types:
            expected_type = field_types[field]
            actual_type = type(value).__name__
            
            # Simple type mapping
            type_map = {
                'string': ['str', 'bytes'],
                'integer': ['int', 'numpy.int64', 'numpy.int32'],
                'number': ['float', 'int', 'numpy.float64', 'numpy.int64'],
                'boolean': ['bool', 'numpy.bool_'],
                'array': ['list', 'tuple'],
            }
            
            if expected_type in type_map:
                if actual_type not in type_map[expected_type]:
                    errors.append(
                        f"Field '{field}' has type '{actual_type}' but expected '{expected_type}'"
                    )
    
    # Check for nulls in required fields
    for field in required_fields:
        if field in row and (row[field] is None or (isinstance(row[field], float) and np.isnan(row[field]))):
            errors.append(f"Required field '{field}' is null")
    
    if errors:
        error_msg = "Row validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    return True