import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yaml
import pandas as pd
from pydantic import BaseModel, ValidationError
import logging

logger = logging.getLogger(__name__)

def load_schema(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a YAML schema definition from a file.
    
    Args:
        schema_path: Path to the schema YAML file.
        
    Returns:
        Dictionary containing the schema definition.
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    
    with open(path, 'r') as f:
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
            actual_type = str(df[col].dtype)
            # Simple type mapping check
            type_map = {
                'int64': ['int', 'integer', 'int64', 'int32'],
                'float64': ['float', 'float64', 'double', 'float32'],
                'object': ['string', 'str', 'object', 'category'],
                'bool': ['bool', 'boolean']
            }
            
            expected_category = None
            for cat, types in type_map.items():
                if expected_type.lower() in types:
                    expected_category = cat
                    break
            
            if expected_category:
                # Check if actual type matches expected category
                is_match = False
                if expected_category in type_map:
                    if actual_type in type_map[expected_category]:
                        is_match = True
                
                # Allow numeric conversions for float/int
                if not is_match:
                    if expected_category == 'float64' and actual_type == 'int64':
                        is_match = True
                    elif expected_category == 'int64' and actual_type == 'float64':
                        # Check if all floats are whole numbers
                        if df[col].apply(lambda x: float(x).is_integer()).all():
                            is_match = True
                
                if not is_match:
                    errors.append(f"Column '{col}' has type {actual_type}, expected {expected_type}")
    
    # Check value constraints if defined
    constraints = schema.get('constraints', {})
    for col, constraint in constraints.items():
        if col in df.columns:
            if 'min' in constraint:
                if (df[col] < constraint['min']).any():
                    errors.append(f"Column '{col}' has values below minimum {constraint['min']}")
            if 'max' in constraint:
                if (df[col] > constraint['max']).any():
                    errors.append(f"Column '{col}' has values above maximum {constraint['max']}")
            if 'allowed_values' in constraint:
                invalid_values = df[~df[col].isin(constraint['allowed_values'])]
                if not invalid_values.empty:
                    errors.append(f"Column '{col}' has disallowed values: {invalid_values.unique().tolist()}")
    
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
    
    # Check field types
    field_types = schema.get('field_types', {})
    for field, expected_type in field_types.items():
        if field in data:
            value = data[field]
            type_map = {
                'string': (str,),
                'integer': (int,),
                'number': (int, float),
                'boolean': (bool,),
                'array': (list,),
                'object': (dict,)
            }
            
            expected_category = None
            for cat, types in type_map.items():
                if expected_type.lower() in cat or expected_type.lower() in [t.__name__ for t in types]:
                    expected_category = cat
                    break
            
            if expected_category:
                if expected_category == 'string' and not isinstance(value, str):
                    errors.append(f"Field '{field}' should be string, got {type(value).__name__}")
                elif expected_category == 'integer' and not isinstance(value, int):
                    errors.append(f"Field '{field}' should be integer, got {type(value).__name__}")
                elif expected_category == 'number' and not isinstance(value, (int, float)):
                    errors.append(f"Field '{field}' should be number, got {type(value).__name__}")
                elif expected_category == 'boolean' and not isinstance(value, bool):
                    errors.append(f"Field '{field}' should be boolean, got {type(value).__name__}")
                elif expected_category == 'array' and not isinstance(value, list):
                    errors.append(f"Field '{field}' should be array, got {type(value).__name__}")
                elif expected_category == 'object' and not isinstance(value, dict):
                    errors.append(f"Field '{field}' should be object, got {type(value).__name__}")
    
    # Check nested objects if defined
    nested_schemas = schema.get('nested_schemas', {})
    for field, nested_schema in nested_schemas.items():
        if field in data and isinstance(data[field], dict):
            is_valid, nested_errors = validate_json_against_schema(data[field], nested_schema)
            if not is_valid:
                for err in nested_errors:
                    errors.append(f"Field '{field}': {err}")
    
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

def validate_pydantic_model(model_class: type[BaseModel], data: Dict[str, Any]) -> tuple:
    """
    Validate a dictionary against a Pydantic model class.
    
    Args:
        model_class: The Pydantic model class to validate against.
        data: The dictionary to validate.
        
    Returns:
        A tuple (is_valid, errors).
    """
    try:
        model = model_class(**data)
        return True, []
    except ValidationError as e:
        errors = [str(err) for err in e.errors()]
        return False, errors

def validate_pydantic_list(models_class: type[BaseModel], data_list: List[Dict[str, Any]]) -> tuple:
    """
    Validate a list of dictionaries against a Pydantic model class.
    
    Args:
        models_class: The Pydantic model class to validate against.
        data_list: The list of dictionaries to validate.
        
    Returns:
        A tuple (is_valid, errors).
    """
    errors = []
    valid_count = 0
    
    for i, item in enumerate(data_list):
        try:
            model = models_class(**item)
            valid_count += 1
        except ValidationError as e:
            for err in e.errors():
                errors.append(f"Item {i}: {err}")
    
    return (valid_count == len(data_list), errors)