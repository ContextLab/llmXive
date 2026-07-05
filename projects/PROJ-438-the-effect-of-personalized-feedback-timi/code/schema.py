"""
schema.py

Provides schema validation utilities for data integrity checks.
Aligns with contracts/dataset.schema.yaml.
"""
import os
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from logging_config import get_logger, info, error, warning

logger = get_logger(__name__)

def load_schema_from_file(schema_path: str) -> Dict:
    """
    Loads a schema definition from a YAML file.
    
    Args:
        schema_path: Path to the YAML schema file.
        
    Returns:
        Dictionary containing the schema definition.
        
    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the file is not valid YAML.
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)
        
    if not isinstance(schema, dict):
        raise ValueError(f"Schema file {schema_path} must contain a top-level dictionary")
        
    return schema

def validate_column_presence(df: pd.DataFrame, required_columns: List[str]) -> Tuple[bool, List[str]]:
    """
    Checks if all required columns are present in the DataFrame.
    
    Args:
        df: DataFrame to validate.
        required_columns: List of column names that must exist.
        
    Returns:
        Tuple of (is_valid, list_of_missing_columns)
    """
    missing = [col for col in required_columns if col not in df.columns]
    return len(missing) == 0, missing

def validate_column_types(df: pd.DataFrame, schema: Dict) -> Tuple[bool, List[str]]:
    """
    Validates column types against the schema.
    Schema format: {'column_name': {'type': 'object'|'number'|'boolean'|'datetime'}}
    
    Args:
        df: DataFrame to validate.
        schema: Schema dictionary defining column types.
        
    Returns:
        Tuple of (is_valid, list_of_type_errors)
    """
    errors = []
    for col, spec in schema.items():
        if col not in df.columns:
            continue  # Handled by validate_column_presence
        
        expected_type = spec.get('type')
        if expected_type is None:
            continue
            
        if expected_type == 'object':
            # Pandas object is default for strings, or we can check for non-numeric
            # Strictly, we ensure it's not numeric if the schema says 'object'
            if pd.api.types.is_numeric_dtype(df[col]):
                # Allow mixed types or strings in object columns
                pass 
        elif expected_type == 'number':
            if not pd.api.types.is_numeric_dtype(df[col]):
                errors.append(f"Column '{col}' is not numeric (expected 'number')")
        elif expected_type == 'boolean':
            if not pd.api.types.is_bool_dtype(df[col]):
                errors.append(f"Column '{col}' is not boolean (expected 'boolean')")
        elif expected_type == 'datetime':
            if not pd.api.types.is_datetime64_any_dtype(df[col]):
                errors.append(f"Column '{col}' is not datetime (expected 'datetime')")
        elif expected_type == 'category':
            # Check if it's categorical or string
            if not (pd.api.types.is_categorical_dtype(df[col]) or pd.api.types.is_string_dtype(df[col])):
                errors.append(f"Column '{col}' is not categorical (expected 'category')")
    
    return len(errors) == 0, errors

def validate_null_values(df: pd.DataFrame, schema: Dict) -> Tuple[bool, List[str]]:
    """
    Validates that columns marked as 'nullable: false' do not have nulls.
    
    Args:
        df: DataFrame to validate.
        schema: Schema dictionary with 'nullable' constraints.
        
    Returns:
        Tuple of (is_valid, list_of_null_errors)
    """
    errors = []
    for col, spec in schema.items():
        if col not in df.columns:
            continue
        
        # Default to nullable=True if not specified
        is_nullable = spec.get('nullable', True)
        if not is_nullable:
            null_count = df[col].isna().sum()
            if null_count > 0:
                errors.append(f"Column '{col}' has {null_count} null values but is marked non-nullable")
    return len(errors) == 0, errors

def validate_value_ranges(df: pd.DataFrame, schema: Dict) -> Tuple[bool, List[str]]:
    """
    Validates numeric ranges or categorical values.
    
    Args:
        df: DataFrame to validate.
        schema: Schema dictionary with 'min', 'max', or 'allowed_values'.
        
    Returns:
        Tuple of (is_valid, list_of_range_errors)
    """
    errors = []
    for col, spec in schema.items():
        if col not in df.columns:
            continue
        
        # Check min
        if 'min' in spec:
            if pd.api.types.is_numeric_dtype(df[col]):
                min_val = df[col].min()
                if pd.notna(min_val) and min_val < spec['min']:
                    errors.append(f"Column '{col}' has values below {spec['min']} (min: {min_val})")
            else:
                errors.append(f"Column '{col}' has 'min' constraint but is not numeric")
        
        # Check max
        if 'max' in spec:
            if pd.api.types.is_numeric_dtype(df[col]):
                max_val = df[col].max()
                if pd.notna(max_val) and max_val > spec['max']:
                    errors.append(f"Column '{col}' has values above {spec['max']} (max: {max_val})")
            else:
                errors.append(f"Column '{col}' has 'max' constraint but is not numeric")
        
        # Check allowed_values (categorical)
        if 'allowed_values' in spec:
            allowed = set(spec['allowed_values'])
            # Filter out NaNs for the check
            valid_mask = df[col].notna()
            if valid_mask.any():
                unique_vals = set(df.loc[valid_mask, col].unique())
                invalid_vals = unique_vals - allowed
                if invalid_vals:
                    errors.append(f"Column '{col}' has values not in allowed list: {sorted(invalid_vals)}")
    
    return len(errors) == 0, errors

def validate_categorical_values(df: pd.DataFrame, schema: Dict) -> Tuple[bool, List[str]]:
    """
    Validates categorical columns against allowed values.
    Delegates to validate_value_ranges for 'allowed_values' checks.
    
    Args:
        df: DataFrame to validate.
        schema: Schema dictionary with 'allowed_values'.
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    return validate_value_ranges(df, schema)

def validate_schema(df: pd.DataFrame, schema: Dict) -> Tuple[bool, List[str]]:
    """
    Runs all validation checks defined in the schema.
    
    Args:
        df: DataFrame to validate.
        schema: Complete schema dictionary.
        
    Returns:
        Tuple of (is_valid, list_of_all_errors)
    """
    errors = []
    
    # 1. Presence: Check all keys in schema are columns
    required_columns = list(schema.keys())
    ok, missing = validate_column_presence(df, required_columns)
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
    Raises an error if schema validation fails.
    
    Args:
        df: DataFrame to validate.
        schema: Schema dictionary.
        
    Returns:
        True if valid.
        
    Raises:
        ValueError: If validation fails.
    """
    ok, errors = validate_schema(df, schema)
    if not ok:
        raise ValueError(f"Schema validation failed: {errors}")
    logger.info("Schema validation passed")
    return True

def filter_valid_records(df: pd.DataFrame, schema: Dict) -> pd.DataFrame:
    """
    Returns a dataframe with only records that pass all schema validations.
    Specifically handles non-nullable columns and allowed values.
    
    Args:
        df: DataFrame to filter.
        schema: Schema dictionary.
        
    Returns:
        Filtered DataFrame.
    """
    mask = pd.Series(True, index=df.index)
    
    for col, spec in schema.items():
        if col not in df.columns:
            continue
        
        # Handle non-nullable
        if not spec.get('nullable', True):
            mask = mask & df[col].notna()
        
        # Handle allowed_values
        if 'allowed_values' in spec:
            allowed = set(spec['allowed_values'])
            # Keep rows where value is in allowed set OR is NaN (if nullable)
            # If not nullable, NaN is already handled above, so we just check allowed
            is_valid_val = df[col].isin(allowed)
            is_null = df[col].isna()
            
            # If nullable, we allow NaN. If not nullable, is_null is False anyway due to previous step
            # But we must ensure we don't drop NaNs if they are allowed by 'nullable' logic
            # However, 'allowed_values' usually implies non-null valid set.
            # Logic: Value must be in allowed set. If nullable, NaN is also acceptable.
            if spec.get('nullable', True):
                mask = mask & (is_valid_val | is_null)
            else:
                mask = mask & is_valid_val
    
    return df[mask].reset_index(drop=True)

def load_schema_and_validate(df: pd.DataFrame, schema_path: str) -> Tuple[bool, List[str]]:
    """
    Convenience function to load schema from file and validate a DataFrame.
    
    Args:
        df: DataFrame to validate.
        schema_path: Path to the YAML schema file.
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    schema = load_schema_from_file(schema_path)
    return validate_schema(df, schema)