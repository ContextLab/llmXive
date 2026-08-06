"""
Schema validation utilities for the OULAD feedback timing analysis pipeline.
Validates data against contracts/dataset.schema.yaml definitions.
"""
import os
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"

def load_schema_from_file(schema_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load schema definition from YAML file."""
    path = schema_path or SCHEMA_PATH
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def get_schema_definition(schema: Dict[str, Any], table_name: str) -> Dict[str, Any]:
    """Get the schema definition for a specific table."""
    if 'tables' not in schema or table_name not in schema['tables']:
        raise ValueError(f"Table '{table_name}' not found in schema")
    return schema['tables'][table_name]

def validate_column_presence(df: pd.DataFrame, required_columns: List[str], table_name: str) -> Tuple[bool, List[str]]:
    """Check that all required columns exist in the DataFrame."""
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        return False, missing
    return True, []

def validate_column_types(df: pd.DataFrame, type_map: Dict[str, str], table_name: str) -> Tuple[bool, List[str]]:
    """Validate that columns have the expected data types."""
    errors = []
    for col, expected_type in type_map.items():
        if col not in df.columns:
            continue  # Missing columns handled by validate_column_presence
        
        actual_type = str(df[col].dtype)
        
        # Map expected types to pandas dtypes
        type_mapping = {
            'int64': ['int64', 'int32', 'Int64', 'Int32'],
            'float64': ['float64', 'float32'],
            'string': ['object', 'string', 'str'],
            'bool': ['bool', 'boolean'],
            'datetime64[ns]': ['datetime64[ns]']
        }
        
        if expected_type in type_mapping:
            if actual_type not in type_mapping[expected_type]:
                errors.append(f"Column '{col}': expected {expected_type}, got {actual_type}")
        elif actual_type != expected_type:
            errors.append(f"Column '{col}': expected {expected_type}, got {actual_type}")
    
    return len(errors) == 0, errors

def validate_null_values(df: pd.DataFrame, nullable_map: Dict[str, bool], table_name: str) -> Tuple[bool, List[str]]:
    """Validate that columns respect nullability constraints."""
    errors = []
    for col, nullable in nullable_map.items():
        if col not in df.columns:
            continue
        
        if not nullable and df[col].isna().any():
            null_count = df[col].isna().sum()
            errors.append(f"Column '{col}' has {null_count} null values but is marked as non-nullable")
    
    return len(errors) == 0, errors

def validate_value_ranges(df: pd.DataFrame, constraints: Dict[str, Dict], table_name: str) -> Tuple[bool, List[str]]:
    """Validate that numeric columns are within specified ranges."""
    errors = []
    for col, constraint in constraints.items():
        if col not in df.columns:
            continue
        
        if 'min' in constraint:
            min_val = constraint['min']
            violations = df[df[col] < min_val]
            if len(violations) > 0:
                errors.append(f"Column '{col}': {len(violations)} values below minimum {min_val}")
        
        if 'max' in constraint:
            max_val = constraint['max']
            violations = df[df[col] > max_val]
            if len(violations) > 0:
                errors.append(f"Column '{col}': {len(violations)} values above maximum {max_val}")
    
    return len(errors) == 0, errors

def validate_categorical_values(df: pd.DataFrame, allowed_values_map: Dict[str, List[str]], table_name: str) -> Tuple[bool, List[str]]:
    """Validate that categorical columns only contain allowed values."""
    errors = []
    for col, allowed in allowed_values_map.items():
        if col not in df.columns:
            continue
        
        invalid_values = set(df[col].unique()) - set(allowed)
        if invalid_values:
            errors.append(f"Column '{col}': found invalid values {invalid_values}, allowed: {allowed}")
    
    return len(errors) == 0, errors

def validate_schema(df: pd.DataFrame, table_name: str, schema: Optional[Dict[str, Any]] = None) -> Tuple[bool, List[str]]:
    """
    Validate a DataFrame against the schema definition for a specific table.
    Returns (is_valid, list_of_errors).
    """
    if schema is None:
        schema = load_schema_from_file()
    
    table_schema = get_schema_definition(schema, table_name)
    
    all_errors = []
    
    # Check required columns
    required_cols = table_schema.get('required_columns', [])
    valid, missing = validate_column_presence(df, required_cols, table_name)
    if not valid:
        all_errors.append(f"Missing required columns: {missing}")
    
    # Check column types
    type_map = table_schema.get('column_types', {})
    valid, type_errors = validate_column_types(df, type_map, table_name)
    if not valid:
        all_errors.extend(type_errors)
    
    # Check nullability
    # Build nullable map: default is nullable=False for required columns unless specified
    column_types = table_schema.get('column_types', {})
    nullable_map = {}
    constraints = table_schema.get('constraints', {})
    
    for col in required_cols:
        # Default to non-nullable unless specified in constraints
        nullable_map[col] = False
        
        # Check if constraint specifies nullable
        if col in constraints:
            # We'll handle explicit nullable in a separate pass if needed
            pass
    
    # Explicitly handle nullable from constraints if present
    for col, constraint in constraints.items():
        if 'nullable' in constraint:
            nullable_map[col] = constraint['nullable']
    
    valid, null_errors = validate_null_values(df, nullable_map, table_name)
    if not valid:
        all_errors.extend(null_errors)
    
    # Check value ranges
    valid, range_errors = validate_value_ranges(df, constraints, table_name)
    if not valid:
        all_errors.extend(range_errors)
    
    # Check categorical values
    allowed_map = {}
    for col, constraint in constraints.items():
        if 'allowed_values' in constraint:
            allowed_map[col] = constraint['allowed_values']
    
    valid, cat_errors = validate_categorical_values(df, allowed_map, table_name)
    if not valid:
        all_errors.extend(cat_errors)
    
    return len(all_errors) == 0, all_errors

def assert_valid_schema(df: pd.DataFrame, table_name: str, schema: Optional[Dict[str, Any]] = None) -> None:
    """Assert that a DataFrame is valid according to the schema. Raises ValueError if invalid."""
    is_valid, errors = validate_schema(df, table_name, schema)
    if not is_valid:
        error_msg = f"Schema validation failed for table '{table_name}':\n" + "\n".join(f"  - {e}" for e in errors)
        raise ValueError(error_msg)

def filter_valid_records(df: pd.DataFrame, table_name: str, schema: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """
    Filter a DataFrame to keep only records that pass all schema validations.
    Returns a tuple of (valid_df, invalid_count).
    """
    if schema is None:
        schema = load_schema_from_file()
    
    table_schema = get_schema_definition(schema, table_name)
    
    # Build mask for valid records
    valid_mask = pd.Series(True, index=df.index)
    
    # Check required columns (drop rows with missing required columns)
    required_cols = table_schema.get('required_columns', [])
    for col in required_cols:
        if col in df.columns:
            valid_mask &= df[col].notna()
        else:
            # If column is missing entirely, all rows are invalid
            valid_mask = pd.Series(False, index=df.index)
            break
    
    # Check value ranges
    constraints = table_schema.get('constraints', {})
    for col, constraint in constraints.items():
        if col not in df.columns:
            continue
        
        if 'min' in constraint:
            valid_mask &= df[col] >= constraint['min']
        
        if 'max' in constraint:
            valid_mask &= df[col] <= constraint['max']
    
    # Check categorical values
    for col, constraint in constraints.items():
        if 'allowed_values' in constraint:
            if col in df.columns:
                valid_mask &= df[col].isin(constraint['allowed_values'])
    
    valid_df = df[valid_mask].copy()
    invalid_count = len(df) - len(valid_df)
    
    return valid_df, invalid_count

def load_schema_and_validate(df: pd.DataFrame, table_name: str) -> bool:
    """
    Convenience function to load schema and validate a DataFrame.
    Returns True if valid, raises ValueError if invalid.
    """
    schema = load_schema_from_file()
    assert_valid_schema(df, table_name, schema)
    return True