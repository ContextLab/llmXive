"""
Schema validation utilities for OULAD dataset processing.
Implements validation functions aligned with contracts/dataset.schema.yaml
"""
import os
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


def load_schema_from_file(schema_path: str) -> Dict[str, Any]:
    """
    Load schema definition from a YAML file.
    
    Args:
        schema_path: Path to the schema YAML file
        
    Returns:
        Dictionary containing the schema definition
        
    Raises:
        FileNotFoundError: If schema file doesn't exist
        yaml.YAMLError: If YAML parsing fails
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def get_schema_definition(schema: Dict[str, Any], artifact_type: str, 
                          artifact_name: str) -> Dict[str, Any]:
    """
    Extract the specific schema definition for an artifact type and name.
    
    Args:
        schema: Full schema dictionary
        artifact_type: 'input' or 'output'
        artifact_name: Name of the artifact (e.g., 'students', 'learners_raw')
        
    Returns:
        Schema definition for the specific artifact
        
    Raises:
        KeyError: If artifact type or name not found in schema
    """
    if artifact_type not in schema:
        raise KeyError(f"Artifact type '{artifact_type}' not found in schema")
    
    if artifact_name not in schema[artifact_type]:
        raise KeyError(f"Artifact '{artifact_name}' not found in {artifact_type}")
    
    return schema[artifact_type][artifact_name]


def validate_column_presence(df: pd.DataFrame, required_columns: List[str]) -> bool:
    """
    Validate that all required columns exist in the DataFrame.
    
    Args:
        df: DataFrame to validate
        required_columns: List of column names that must be present
        
    Returns:
        True if all required columns exist, False otherwise
    """
    df_columns = set(df.columns)
    required_set = set(required_columns)
    return required_set.issubset(df_columns)


def validate_column_types(df: pd.DataFrame, types_map: Dict[str, str]) -> bool:
    """
    Validate that columns have the expected data types.
    
    Args:
        df: DataFrame to validate
        types_map: Dictionary mapping column names to expected dtypes
        
    Returns:
        True if all types match, False otherwise
    """
    for col, expected_type in types_map.items():
        if col not in df.columns:
            return False
        
        actual_type = str(df[col].dtype)
        if actual_type != expected_type:
            return False
    
    return True


def validate_null_values(df: pd.DataFrame, critical_columns: List[str]) -> bool:
    """
    Validate that critical columns have no null values.
    
    Args:
        df: DataFrame to validate
        critical_columns: List of column names that must not contain nulls
        
    Returns:
        True if no nulls in critical columns, False otherwise
    """
    for col in critical_columns:
        if col not in df.columns:
            return False
        if df[col].isna().any():
            return False
    
    return True


def validate_value_ranges(df: pd.DataFrame, ranges_map: Dict[str, Dict[str, float]]) -> bool:
    """
    Validate that numeric columns fall within specified ranges.
    
    Args:
        df: DataFrame to validate
        ranges_map: Dictionary mapping column names to {'min': float, 'max': float}
        
    Returns:
        True if all values in range, False otherwise
    """
    for col, range_spec in ranges_map.items():
        if col not in df.columns:
            return False
        
        min_val = range_spec.get('min', float('-inf'))
        max_val = range_spec.get('max', float('inf'))
        
        col_min = df[col].min()
        col_max = df[col].max()
        
        if col_min < min_val or col_max > max_val:
            return False
    
    return True


def validate_categorical_values(df: pd.DataFrame, 
                                categorical_map: Dict[str, List[Any]]) -> bool:
    """
    Validate that categorical columns only contain allowed values.
    
    Args:
        df: DataFrame to validate
        categorical_map: Dictionary mapping column names to list of allowed values
        
    Returns:
        True if all values are allowed, False otherwise
    """
    for col, allowed_values in categorical_map.items():
        if col not in df.columns:
            return False
        
        allowed_set = set(allowed_values)
        actual_values = set(df[col].unique())
        
        if not actual_values.issubset(allowed_set):
            return False
    
    return True


def validate_schema(df: pd.DataFrame, schema_def: Dict[str, Any]) -> bool:
    """
    Comprehensive schema validation for a DataFrame.
    
    Args:
        df: DataFrame to validate
        schema_def: Schema definition dictionary containing:
            - required_columns: List of required column names
            - types: Dictionary of column -> expected dtype
            - critical_columns: List of columns that cannot have nulls
            - value_ranges: Optional dictionary of column -> {min, max}
            - categorical_values: Optional dictionary of column -> allowed values
        
    Returns:
        True if all validations pass, False otherwise
    """
    # Validate column presence
    if 'required_columns' in schema_def:
        if not validate_column_presence(df, schema_def['required_columns']):
            return False
    
    # Validate column types
    if 'types' in schema_def:
        if not validate_column_types(df, schema_def['types']):
            return False
    
    # Validate null values in critical columns
    if 'critical_columns' in schema_def:
        if not validate_null_values(df, schema_def['critical_columns']):
            return False
    
    # Validate value ranges
    if 'value_ranges' in schema_def:
        if not validate_value_ranges(df, schema_def['value_ranges']):
            return False
    
    # Validate categorical values
    if 'categorical_values' in schema_def:
        if not validate_categorical_values(df, schema_def['categorical_values']):
            return False
    
    return True


def assert_valid_schema(df: pd.DataFrame, schema_def: Dict[str, Any], 
                        artifact_name: str = "unknown") -> None:
    """
    Assert that a DataFrame conforms to the schema, raising ValueError on failure.
    
    Args:
        df: DataFrame to validate
        schema_def: Schema definition dictionary
        artifact_name: Name of the artifact for error messages
        
    Raises:
        ValueError: If validation fails
    """
    if not validate_schema(df, schema_def):
        missing_cols = []
        if 'required_columns' in schema_def:
            for col in schema_def['required_columns']:
                if col not in df.columns:
                    missing_cols.append(col)
        
        null_cols = []
        if 'critical_columns' in schema_def:
            for col in schema_def['critical_columns']:
                if col in df.columns and df[col].isna().any():
                    null_cols.append(col)
        
        error_msg = f"Schema validation failed for '{artifact_name}':\n"
        if missing_cols:
            error_msg += f"  Missing columns: {missing_cols}\n"
        if null_cols:
            error_msg += f"  Null values in critical columns: {null_cols}\n"
        
        raise ValueError(error_msg)


def filter_valid_records(df: pd.DataFrame, schema_def: Dict[str, Any]) -> pd.DataFrame:
    """
    Filter a DataFrame to keep only records that pass schema validation.
    
    Args:
        df: DataFrame to filter
        schema_def: Schema definition dictionary
        
    Returns:
        Filtered DataFrame with only valid records
    """
    mask = pd.Series(True, index=df.index)
    
    # Filter by critical columns null check
    if 'critical_columns' in schema_def:
        for col in schema_def['critical_columns']:
            if col in df.columns:
                mask = mask & (~df[col].isna())
    
    # Filter by value ranges
    if 'value_ranges' in schema_def:
        for col, range_spec in schema_def['value_ranges'].items():
            if col in df.columns:
                min_val = range_spec.get('min', float('-inf'))
                max_val = range_spec.get('max', float('inf'))
                mask = mask & (df[col] >= min_val) & (df[col] <= max_val)
    
    # Filter by categorical values
    if 'categorical_values' in schema_def:
        for col, allowed_values in schema_def['categorical_values'].items():
            if col in df.columns:
                mask = mask & df[col].isin(allowed_values)
    
    return df[mask]


def load_schema_and_validate(schema_path: str, artifact_type: str, 
                             artifact_name: str, df: pd.DataFrame) -> bool:
    """
    Load schema from file and validate a DataFrame against it.
    
    Args:
        schema_path: Path to schema YAML file
        artifact_type: 'input' or 'output'
        artifact_name: Name of the artifact
        df: DataFrame to validate
        
    Returns:
        True if validation passes, False otherwise
        
    Raises:
        FileNotFoundError: If schema file not found
        KeyError: If artifact not found in schema
    """
    schema = load_schema_from_file(schema_path)
    schema_def = get_schema_definition(schema, artifact_type, artifact_name)
    return validate_schema(df, schema_def)
