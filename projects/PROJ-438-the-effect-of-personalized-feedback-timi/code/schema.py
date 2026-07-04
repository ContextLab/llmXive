"""
schema.py

Provides schema validation utilities for data integrity checks.
"""
import os
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from logging_config import get_logger, info, error, warning

def load_schema_from_file(schema_path: str) -> Dict:
    """
    Loads a schema definition from a YAML file.
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def validate_column_presence(df: pd.DataFrame, required_columns: List[str]) -> Tuple[bool, List[str]]:
    """
    Checks if all required columns are present in the DataFrame.
    """
    missing = [col for col in required_columns if col not in df.columns]
    return len(missing) == 0, missing

def validate_column_types(df: pd.DataFrame, schema: Dict) -> Tuple[bool, List[str]]:
    """
    Validates column types against the schema.
    Schema format: {'column_name': {'type': 'object|number|boolean|datetime'}}
    """
    errors = []
    for col, spec in schema.items():
        if col not in df.columns:
            continue # Handled by validate_column_presence
        
        expected_type = spec.get('type')
        if expected_type == 'object':
            # Pandas object is default for strings
            pass
        elif expected_type == 'number':
            if not pd.api.types.is_numeric_dtype(df[col]):
                errors.append(f"Column {col} is not numeric")
        elif expected_type == 'boolean':
            if not pd.api.types.is_bool_dtype(df[col]):
                errors.append(f"Column {col} is not boolean")
        elif expected_type == 'datetime':
            if not pd.api.types.is_datetime64_any_dtype(df[col]):
                errors.append(f"Column {col} is not datetime")
    
    return len(errors) == 0, errors

def validate_null_values(df: pd.DataFrame, schema: Dict) -> Tuple[bool, List[str]]:
    """
    Validates that columns marked as 'nullable: false' do not have nulls.
    """
    errors = []
    for col, spec in schema.items():
        if col not in df.columns:
            continue
        if spec.get('nullable', True) == False:
            if df[col].isna().any():
                errors.append(f"Column {col} has null values but is marked non-nullable")
    return len(errors) == 0, errors

def validate_value_ranges(df: pd.DataFrame, schema: Dict) -> Tuple[bool, List[str]]:
    """
    Validates numeric ranges or categorical values.
    """
    errors = []
    for col, spec in schema.items():
        if col not in df.columns:
            continue
        
        if 'min' in spec:
            if df[col].min() < spec['min']:
                errors.append(f"Column {col} has values below {spec['min']}")
        if 'max' in spec:
            if df[col].max() > spec['max']:
                errors.append(f"Column {col} has values above {spec['max']}")
        if 'allowed_values' in spec:
            invalid = df[~df[col].isin(spec['allowed_values'])]
            if not invalid.empty:
                errors.append(f"Column {col} has values not in allowed list")
    
    return len(errors) == 0, errors

def validate_categorical_values(df: pd.DataFrame, schema: Dict) -> Tuple[bool, List[str]]:
    """
    Validates categorical columns against allowed values.
    """
    return validate_value_ranges(df, schema) # Reuse logic

def validate_schema(df: pd.DataFrame, schema: Dict) -> Tuple[bool, List[str]]:
    """
    Runs all validation checks.
    """
    errors = []
    
    # 1. Presence
    required = list(schema.keys())
    ok, missing = validate_column_presence(df, required)
    if not ok:
        errors.extend([f"Missing column: {m}" for m in missing])
    
    # 2. Types
    ok, type_errors = validate_column_types(df, schema)
    if not ok:
        errors.extend(type_errors)
    
    # 3. Nulls
    ok, null_errors = validate_null_values(df, schema)
    if not ok:
        errors.extend(null_errors)
    
    # 4. Ranges/Categories
    ok, range_errors = validate_value_ranges(df, schema)
    if not ok:
        errors.extend(range_errors)
    
    return len(errors) == 0, errors

def assert_valid_schema(df: pd.DataFrame, schema: Dict) -> bool:
    """
    Raises an error if schema is invalid.
    """
    ok, errors = validate_schema(df, schema)
    if not ok:
        raise ValueError(f"Schema validation failed: {errors}")
    return True

def filter_valid_records(df: pd.DataFrame, schema: Dict) -> pd.DataFrame:
    """
    Returns a dataframe with only records that pass all schema validations.
    """
    # Simple implementation: drop rows with nulls in non-nullable columns
    mask = pd.Series(True, index=df.index)
    for col, spec in schema.items():
        if col not in df.columns:
            continue
        if spec.get('nullable', True) == False:
            mask = mask & df[col].notna()
    return df[mask]
