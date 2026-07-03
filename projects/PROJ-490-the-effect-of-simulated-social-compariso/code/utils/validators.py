"""
Schema validation utilities for the simulated social comparison project.

This module provides functions to validate datasets and outputs against
the schema contracts defined in the contracts/ directory.
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
import pandas as pd
from pydantic import BaseModel, ValidationError

# Try to import jsonschema, fallback to basic validation if not available
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

from code.utils.logger import get_logger

logger = get_logger(__name__)


def load_schema(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a YAML schema definition from a file.
    
    Args:
        schema_path: Path to the schema YAML file.
        
    Returns:
        Dictionary containing the schema definition.
        
    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the schema file is not valid YAML.
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
        
    with open(path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)
        
    return schema


def validate_dataframe_schema(
    df: pd.DataFrame,
    schema: Dict[str, Any],
    strict: bool = False
) -> Dict[str, Any]:
    """
    Validate a pandas DataFrame against a schema definition.
    
    Args:
        df: The DataFrame to validate.
        schema: The schema definition dictionary.
        strict: If True, raise an error if columns exist in df but not in schema.
                
    Returns:
        A dictionary with validation results:
        - 'valid': bool
        - 'errors': List of error messages
        - 'warnings': List of warning messages
    """
    errors = []
    warnings = []
    
    # Check required columns
    required_columns = schema.get('required_columns', [])
    actual_columns = set(df.columns)
    required_set = set(required_columns)
    
    missing_columns = required_set - actual_columns
    if missing_columns:
        errors.append(f"Missing required columns: {sorted(missing_columns)}")
        
    # Check for unexpected columns in strict mode
    if strict:
        schema_columns = set(required_columns + schema.get('optional_columns', []))
        extra_columns = actual_columns - schema_columns
        if extra_columns:
            warnings.append(f"Unexpected columns in strict mode: {sorted(extra_columns)}")
            
    # Validate column types if specified
    column_types = schema.get('column_types', {})
    for col_name, expected_type in column_types.items():
        if col_name in actual_columns:
            actual_type = df[col_name].dtype
            # Simple type mapping
            type_map = {
                'int': ['int64', 'int32', 'int16', 'int8'],
                'float': ['float64', 'float32'],
                'string': ['object', 'string'],
                'bool': ['bool'],
                'datetime': ['datetime64[ns]']
            }
            
            expected_types = type_map.get(expected_type, [expected_type])
            if str(actual_type) not in expected_types:
                errors.append(
                    f"Column '{col_name}' has type '{actual_type}', "
                    f"expected one of: {expected_types}"
                )
                
    # Validate value constraints if specified
    constraints = schema.get('constraints', {})
    for col_name, col_constraints in constraints.items():
        if col_name not in actual_columns:
            continue
            
        series = df[col_name]
        
        # Check for nulls if not allowed
        if col_constraints.get('allow_null') is False:
            null_count = series.isna().sum()
            if null_count > 0:
                errors.append(
                    f"Column '{col_name}' contains {null_count} null values "
                    f"(nulls not allowed)"
                )
                
        # Check value range
        if 'min_value' in col_constraints:
            min_val = col_constraints['min_value']
            non_null = series.dropna()
            if len(non_null) > 0 and non_null.min() < min_val:
                errors.append(
                    f"Column '{col_name}' has values below minimum {min_val}"
                )
                
        if 'max_value' in col_constraints:
            max_val = col_constraints['max_value']
            non_null = series.dropna()
            if len(non_null) > 0 and non_null.max() > max_val:
                errors.append(
                    f"Column '{col_name}' has values above maximum {max_val}"
                )
                
        # Check allowed values
        if 'allowed_values' in col_constraints:
            allowed = set(col_constraints['allowed_values'])
            non_null = series.dropna()
            invalid_values = set(non_null.unique()) - allowed
            if invalid_values:
                errors.append(
                    f"Column '{col_name}' contains invalid values: {invalid_values}"
                )
                
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }


def validate_json_against_schema(
    data: Dict[str, Any],
    schema: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate a JSON/dictionary object against a JSON schema.
    
    Args:
        data: The data to validate.
        schema: The JSON schema definition.
        
    Returns:
        A dictionary with validation results:
        - 'valid': bool
        - 'errors': List of error messages
    """
    if not HAS_JSONSCHEMA:
        logger.warning("jsonschema not installed, performing basic validation only")
        # Basic validation without jsonschema
        errors = []
        required = schema.get('required', [])
        for field in required:
            if field not in data:
                errors.append(f"Missing required field: {field}")
                
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
        
    try:
        jsonschema.validate(instance=data, schema=schema)
        return {'valid': True, 'errors': []}
    except jsonschema.ValidationError as e:
        return {
            'valid': False,
            'errors': [e.message]
        }


def validate_dataset(
    data_path: Union[str, Path],
    schema_path: Union[str, Path],
    file_format: str = 'csv'
) -> Dict[str, Any]:
    """
    Validate a dataset file against a schema.
    
    Args:
        data_path: Path to the dataset file.
        schema_path: Path to the schema definition file.
        file_format: Format of the data file ('csv', 'parquet', 'json').
        
    Returns:
        Validation results dictionary.
    """
    data_path = Path(data_path)
    schema_path = Path(schema_path)
    
    # Load schema
    schema = load_schema(schema_path)
    
    # Load data
    if file_format == 'csv':
        df = pd.read_csv(data_path)
    elif file_format == 'parquet':
        df = pd.read_parquet(data_path)
    elif file_format == 'json':
        df = pd.read_json(data_path)
    else:
        raise ValueError(f"Unsupported file format: {file_format}")
        
    # Validate
    return validate_dataframe_schema(df, schema)


def validate_output(
    output_path: Union[str, Path],
    schema_path: Union[str, Path]
) -> Dict[str, Any]:
    """
    Validate an output JSON file against a schema.
    
    Args:
        output_path: Path to the output JSON file.
        schema_path: Path to the schema definition file.
        
    Returns:
        Validation results dictionary.
    """
    output_path = Path(output_path)
    schema_path = Path(schema_path)
    
    # Load schema
    schema = load_schema(schema_path)
    
    # Load data
    with open(output_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # Validate
    return validate_json_against_schema(data, schema)


def assert_valid(
    validation_result: Dict[str, Any],
    raise_on_error: bool = True
) -> None:
    """
    Assert that a validation result is valid, optionally raising an error.
    
    Args:
        validation_result: The result from a validation function.
        raise_on_error: If True, raise ValueError if validation fails.
        
    Raises:
        ValueError: If validation fails and raise_on_error is True.
    """
    if not validation_result.get('valid', False):
        error_msg = "Validation failed:\n"
        for error in validation_result.get('errors', []):
            error_msg += f"  - {error}\n"
        for warning in validation_result.get('warnings', []):
            error_msg += f"  - WARNING: {warning}\n"
            
        if raise_on_error:
            raise ValueError(error_msg)
            
        logger.warning(error_msg)