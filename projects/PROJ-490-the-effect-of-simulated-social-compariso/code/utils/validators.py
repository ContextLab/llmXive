import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yaml
import pandas as pd
from pydantic import BaseModel, ValidationError

def load_schema(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a YAML schema definition from a file.
    
    Args:
        schema_path: Path to the schema YAML file.
        
    Returns:
        Dictionary containing the schema definition.
    """
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_dataframe_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> tuple:
    """
    Validate that a DataFrame matches the expected schema.
    
    Args:
        df: The pandas DataFrame to validate.
        schema: The schema dictionary defining expected columns and types.
        
    Returns:
        A tuple (is_valid, errors) where is_valid is a boolean and errors is a list of error messages.
    """
    errors = []
    
    # Check required columns
    required_columns = schema.get('required_columns', [])
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        errors.append(f"Missing required columns: {missing_columns}")
    
    # Check column types
    column_types = schema.get('column_types', {})
    for col, expected_type in column_types.items():
        if col in df.columns:
            actual_type = df[col].dtype
            # Simple type mapping check
            type_map = {
                'int64': ['int', 'integer', 'int64'],
                'float64': ['float', 'float64', 'double'],
                'object': ['string', 'str', 'object'],
                'bool': ['bool', 'boolean']
            }
            
            expected_category = None
            for cat, types in type_map.items():
                if expected_type.lower() in types:
                    expected_category = cat
                    break
            
            if expected_category and actual_type not in type_map.get(expected_category, []):
                # Allow numeric conversions for float/int
                if expected_category == 'float64' and actual_type == 'int64':
                    continue
                if expected_category == 'int64' and actual_type == 'float64':
                    # Check if all floats are whole numbers
                    if not df[col].apply(lambda x: float(x).is_integer()).all():
                        errors.append(f"Column '{col}' should be integer but is {actual_type}")
                    continue
                
                errors.append(f"Column '{col}' has type {actual_type}, expected {expected_type}")
        
    return (len(errors) == 0, errors)

def validate_json_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> tuple:
    """
    Validate a JSON-like dictionary against a schema.
    
    Args:
        data: The dictionary to validate.
        schema: The schema dictionary.
        
    Returns:
        A tuple (is_valid, errors).
    """
    errors = []
    
    required_fields = schema.get('required_fields', [])
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        errors.append(f"Missing required fields: {missing_fields}")
        
    return (len(errors) == 0, errors)

def validate_dataset(df: pd.DataFrame, schema_path: Union[str, Path]) -> tuple:
    """
    High-level function to validate a dataset against a schema file.
    
    Args:
        df: The DataFrame to validate.
        schema_path: Path to the schema file.
        
    Returns:
        A tuple (is_valid, errors).
    """
    schema = load_schema(schema_path)
    return validate_dataframe_schema(df, schema)

def validate_output(data: Any, schema_path: Union[str, Path]) -> tuple:
    """
    Validate output data (DataFrame or Dict) against a schema.
    
    Args:
        data: The data to validate (DataFrame or dict).
        schema_path: Path to the schema file.
        
    Returns:
        A tuple (is_valid, errors).
    """
    schema = load_schema(schema_path)
    
    if isinstance(data, pd.DataFrame):
        return validate_dataframe_schema(data, schema)
    elif isinstance(data, dict):
        return validate_json_against_schema(data, schema)
    else:
        return False, [f"Unsupported data type: {type(data)}"]

def assert_valid(df: pd.DataFrame, schema_path: Union[str, Path]) -> None:
    """
    Assert that a DataFrame is valid against a schema. Raises AssertionError if invalid.
    
    Args:
        df: The DataFrame to validate.
        schema_path: Path to the schema file.
    """
    is_valid, errors = validate_dataset(df, schema_path)
    if not is_valid:
        raise AssertionError(f"Schema validation failed: {errors}")
