"""
Schema validation utilities for the OULAD Feedback Timing Analysis pipeline.
Aligns with contracts/dataset.schema.yaml.
"""
import os
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from logging_config import get_logger, info, warning, error, debug

logger = get_logger(__name__)

# Default path to the schema file relative to project root
SCHEMA_PATH = Path("contracts/dataset.schema.yaml")

def load_schema_from_file(schema_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the dataset schema from a YAML file.
    
    Args:
        schema_path: Path to the schema YAML file. Defaults to contracts/dataset.schema.yaml.
        
    Returns:
        Dictionary containing the schema definition.
        
    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the schema file is not valid YAML.
    """
    if schema_path is None:
        # Resolve relative to project root (assumed to be 2 levels up from code/)
        base_dir = Path(__file__).resolve().parent.parent
        schema_path = base_dir / "contracts" / "dataset.schema.yaml"
        
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")
        
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
        
    logger.info(f"Loaded schema from {schema_path}")
    return schema


def validate_column_presence(df: pd.DataFrame, required_columns: List[str], schema_name: str) -> Tuple[bool, List[str]]:
    """
    Validate that all required columns are present in the DataFrame.
    
    Args:
        df: The DataFrame to validate.
        required_columns: List of required column names.
        schema_name: Name of the schema being validated (for logging).
        
    Returns:
        Tuple of (is_valid, list_of_missing_columns).
    """
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        error(f"Schema validation failed for {schema_name}: Missing columns: {missing}")
        return False, missing
    info(f"Schema validation passed for {schema_name}: All required columns present.")
    return True, []


def validate_column_types(df: pd.DataFrame, type_map: Dict[str, str], schema_name: str) -> Tuple[bool, List[str]]:
    """
    Validate that columns match expected types.
    
    Args:
        df: The DataFrame to validate.
        type_map: Dictionary mapping column names to expected types (string, integer, float, boolean).
        schema_name: Name of the schema being validated.
        
    Returns:
        Tuple of (is_valid, list_of_type_errors).
    """
    errors = []
    for col, expected_type in type_map.items():
        if col not in df.columns:
            continue  # Handled by presence check
            
        actual_dtype = df[col].dtype
        valid = False
        
        if expected_type == 'string':
            valid = pd.api.types.is_string_dtype(actual_dtype) or actual_dtype == object
        elif expected_type == 'integer':
            valid = pd.api.types.is_integer_dtype(actual_dtype)
        elif expected_type == 'float':
            valid = pd.api.types.is_float_dtype(actual_dtype)
        elif expected_type == 'boolean':
            valid = pd.api.types.is_bool_dtype(actual_dtype)
            
        if not valid:
            errors.append(f"Column '{col}' expected type '{expected_type}', got '{actual_dtype}'")
            
    if errors:
        error(f"Schema validation failed for {schema_name}: {errors}")
        return False, errors
    info(f"Schema validation passed for {schema_name}: All column types correct.")
    return True, []


def validate_null_values(df: pd.DataFrame, constraints: Dict[str, Dict], schema_name: str) -> Tuple[bool, List[str]]:
    """
    Validate null constraints defined in the schema.
    
    Args:
        df: The DataFrame to validate.
        constraints: Dictionary of column constraints (e.g., allow_null).
        schema_name: Name of the schema being validated.
        
    Returns:
        Tuple of (is_valid, list_of_null_errors).
    """
    errors = []
    for col, rules in constraints.items():
        if col not in df.columns:
            continue
            
        allow_null = rules.get('allow_null', True)
        if not allow_null:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                errors.append(f"Column '{col}' has {null_count} null values but allow_null is False")
                
    if errors:
        error(f"Schema validation failed for {schema_name}: {errors}")
        return False, errors
    info(f"Schema validation passed for {schema_name}: Null constraints satisfied.")
    return True, []


def validate_value_ranges(df: pd.DataFrame, constraints: Dict[str, Dict], schema_name: str) -> Tuple[bool, List[str]]:
    """
    Validate value ranges (min/max) defined in the schema.
    
    Args:
        df: The DataFrame to validate.
        constraints: Dictionary of column constraints (e.g., min, max).
        schema_name: Name of the schema being validated.
        
    Returns:
        Tuple of (is_valid, list_of_range_errors).
    """
    errors = []
    for col, rules in constraints.items():
        if col not in df.columns:
            continue
            
        if 'min' in rules:
            min_val = df[col].min()
            if min_val < rules['min']:
                errors.append(f"Column '{col}' has min value {min_val} below threshold {rules['min']}")
                
        if 'max' in rules:
            max_val = df[col].max()
            if max_val > rules['max']:
                errors.append(f"Column '{col}' has max value {max_val} above threshold {rules['max']}")
                
    if errors:
        error(f"Schema validation failed for {schema_name}: {errors}")
        return False, errors
    info(f"Schema validation passed for {schema_name}: Value ranges satisfied.")
    return True, []


def validate_categorical_values(df: pd.DataFrame, constraints: Dict[str, Dict], schema_name: str) -> Tuple[bool, List[str]]:
    """
    Validate that categorical columns only contain allowed values.
    
    Args:
        df: The DataFrame to validate.
        constraints: Dictionary of column constraints (e.g., allowed_values).
        schema_name: Name of the schema being validated.
        
    Returns:
        Tuple of (is_valid, list_of_categorical_errors).
    """
    errors = []
    for col, rules in constraints.items():
        if col not in df.columns:
            continue
            
        if 'allowed_values' in rules:
            allowed = set(rules['allowed_values'])
            unique_vals = set(df[col].dropna().unique())
            invalid = unique_vals - allowed
            if invalid:
                errors.append(f"Column '{col}' contains invalid values: {invalid}")
                
    if errors:
        error(f"Schema validation failed for {schema_name}: {errors}")
        return False, errors
    info(f"Schema validation passed for {schema_name}: Categorical values valid.")
    return True, []


def validate_schema(df: pd.DataFrame, schema_def: Dict[str, Any], schema_name: str) -> bool:
    """
    Run all validation checks against a DataFrame using a specific schema definition.
    
    Args:
        df: The DataFrame to validate.
        schema_def: The specific schema definition (e.g., schema_def['learners_raw']).
        schema_name: Name of the schema being validated.
        
    Returns:
        True if all validations pass, False otherwise.
    """
    if schema_name not in schema_def:
        error(f"Schema definition '{schema_name}' not found in schema.")
        return False
        
    spec = schema_def[schema_name]
    all_valid = True
    
    # 1. Column Presence
    if 'required_columns' in spec:
        valid, _ = validate_column_presence(df, spec['required_columns'], schema_name)
        if not valid:
            all_valid = False
            
    # 2. Column Types
    if 'column_types' in spec:
        valid, _ = validate_column_types(df, spec['column_types'], schema_name)
        if not valid:
            all_valid = False
            
    # 3. Constraints (Null, Range, Categorical)
    if 'constraints' in spec:
        constraints = spec['constraints']
        
        # Null
        valid, _ = validate_null_values(df, constraints, schema_name)
        if not valid:
            all_valid = False
            
        # Range
        valid, _ = validate_value_ranges(df, constraints, schema_name)
        if not valid:
            all_valid = False
            
        # Categorical
        valid, _ = validate_categorical_values(df, constraints, schema_name)
        if not valid:
            all_valid = False
            
    return all_valid


def assert_valid_schema(df: pd.DataFrame, schema_def: Dict[str, Any], schema_name: str) -> None:
    """
    Validate schema and raise AssertionError if invalid.
    
    Args:
        df: The DataFrame to validate.
        schema_def: The schema definition dictionary.
        schema_name: Name of the schema being validated.
        
    Raises:
        AssertionError: If validation fails.
    """
    if not validate_schema(df, schema_def, schema_name):
        raise AssertionError(f"DataFrame does not conform to schema '{schema_name}'")


def filter_valid_records(df: pd.DataFrame, schema_def: Dict[str, Any], schema_name: str) -> pd.DataFrame:
    """
    Filter a DataFrame to keep only records that satisfy the schema constraints.
    Currently implements null filtering and range clipping if specified.
    
    Args:
        df: The DataFrame to filter.
        schema_def: The schema definition dictionary.
        schema_name: Name of the schema being validated.
        
    Returns:
        Filtered DataFrame.
    """
    if schema_name not in schema_def:
        return df
        
    spec = schema_def[schema_name]
    df_filtered = df.copy()
    
    if 'constraints' in spec:
        constraints = spec['constraints']
        
        for col, rules in constraints.items():
            if col not in df_filtered.columns:
                continue
                
            # Filter Nulls
            if not rules.get('allow_null', True):
                initial_count = len(df_filtered)
                df_filtered = df_filtered.dropna(subset=[col])
                dropped = initial_count - len(df_filtered)
                if dropped > 0:
                    warning(f"Dropped {dropped} rows from {schema_name} due to nulls in '{col}'")
                    
            # Filter Ranges (Drop out of bounds)
            if 'min' in rules:
                mask = df_filtered[col] >= rules['min']
                dropped = (~mask).sum()
                if dropped > 0:
                    warning(f"Dropped {dropped} rows from {schema_name} due to min constraint on '{col}'")
                    df_filtered = df_filtered[mask]
                    
            if 'max' in rules:
                mask = df_filtered[col] <= rules['max']
                dropped = (~mask).sum()
                if dropped > 0:
                    warning(f"Dropped {dropped} rows from {schema_name} due to max constraint on '{col}'")
                    df_filtered = df_filtered[mask]
                    
    return df_filtered


def load_schema_and_validate(df: pd.DataFrame, schema_name: str, schema_path: Optional[Path] = None) -> bool:
    """
    Convenience function to load schema from file and validate a DataFrame.
    
    Args:
        df: The DataFrame to validate.
        schema_name: Name of the schema (e.g., 'learners_raw').
        schema_path: Optional path to schema file.
        
    Returns:
        True if valid, False otherwise.
    """
    try:
        schema = load_schema_from_file(schema_path)
        return validate_schema(df, schema, schema_name)
    except Exception as e:
        error(f"Error during schema validation: {e}")
        return False

# Utility to get the schema definition directly for programmatic use
def get_schema_definition(schema_name: str) -> Dict[str, Any]:
    """
    Load the full schema and return the definition for a specific table.
    
    Args:
        schema_name: Name of the schema table (e.g., 'learners_raw').
        
    Returns:
        The definition dictionary for the requested schema table.
    """
    schema = load_schema_from_file()
    if schema_name not in schema:
        raise KeyError(f"Schema '{schema_name}' not found in dataset.schema.yaml")
    return schema[schema_name]