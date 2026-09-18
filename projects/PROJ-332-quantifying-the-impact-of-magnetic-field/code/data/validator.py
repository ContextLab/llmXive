"""
Schema validation module for the plasma confinement analysis pipeline.

This module provides functions to validate input and output data against
defined YAML schema contracts to ensure data integrity before processing.
"""

import logging
import json
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import yaml
import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)

# Default paths to schema files
DATASET_SCHEMA_PATH = Path("contracts/dataset.schema.yaml")
OUTPUT_SCHEMA_PATH = Path("contracts/output.schema.yaml")

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """
    Load a schema definition from a YAML file.
    
    Args:
        schema_path: Path to the YAML schema file.
        
    Returns:
        Dictionary containing the schema definition.
        
    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the schema file is not valid YAML.
    """
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)
        
    logger.info(f"Loaded schema from {schema_path}")
    return schema

def validate_dataframe_against_schema(
    df: pd.DataFrame, 
    schema: Dict[str, Any], 
    strict: bool = True
) -> Tuple[bool, List[str]]:
    """
    Validate a pandas DataFrame against a JSON Schema-like definition.
    
    Args:
        df: The DataFrame to validate.
        schema: The schema definition dictionary.
        strict: If True, fail if columns exist that are not in schema properties.
                
    Returns:
        A tuple (is_valid, list_of_errors).
    """
    errors = []
    
    # Check required columns
    required_columns = schema.get('required', [])
    for col in required_columns:
        if col not in df.columns:
            errors.append(f"Missing required column: '{col}'")
    
    if errors:
        return False, errors
    
    # Validate column types and constraints
    properties = schema.get('properties', {})
    
    for col_name, col_schema in properties.items():
        if col_name not in df.columns:
            continue
        
        col = df[col_name]
        col_type = col_schema.get('type')
        
        # Type checking
        if col_type == 'integer':
            if not pd.api.types.is_integer_dtype(col):
                # Allow float that are actually integers
                if not pd.api.types.is_float_dtype(col) or not (col == col.astype(int)).all():
                    errors.append(f"Column '{col_name}' must be integer, found {col.dtype}")
        elif col_type == 'number':
            if not (pd.api.types.is_float_dtype(col) or pd.api.types.is_integer_dtype(col)):
                errors.append(f"Column '{col_name}' must be numeric, found {col.dtype}")
        elif col_type == 'string':
            if not pd.api.types.is_string_dtype(col) and not pd.api.types.is_object_dtype(col):
                errors.append(f"Column '{col_name}' must be string, found {col.dtype}")
        
        # Enum checking
        if 'enum' in col_schema:
            valid_values = set(col_schema['enum'])
            invalid_values = set(df[col_name].dropna().unique()) - valid_values
            if invalid_values:
                errors.append(f"Column '{col_name}' contains invalid values: {invalid_values}")
    
    # Strict mode: check for extra columns
    if strict:
        allowed_columns = set(properties.keys())
        actual_columns = set(df.columns)
        extra_columns = actual_columns - allowed_columns
        if extra_columns:
            errors.append(f"Unexpected columns found: {extra_columns}")
    
    return len(errors) == 0, errors

def validate_input_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate a DataFrame against the input dataset schema.
    
    Args:
        df: The DataFrame to validate.
        
    Returns:
        A tuple (is_valid, list_of_errors).
    """
    try:
        schema = load_schema(DATASET_SCHEMA_PATH)
        return validate_dataframe_against_schema(df, schema)
    except Exception as e:
        logger.error(f"Failed to validate input schema: {e}")
        return False, [str(e)]

def validate_output_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate a DataFrame against the output schema.
    
    Args:
        df: The DataFrame to validate.
        
    Returns:
        A tuple (is_valid, list_of_errors).
    """
    try:
        schema = load_schema(OUTPUT_SCHEMA_PATH)
        return validate_dataframe_against_schema(df, schema)
    except Exception as e:
        logger.error(f"Failed to validate output schema: {e}")
        return False, [str(e)]

def validate_parsed_data(df: pd.DataFrame) -> bool:
    """
    Main entry point for validating parsed data before further processing.
    
    This function is called by the preprocessing pipeline to ensure that
    the data retrieved and parsed from MDSplus conforms to the expected schema.
    
    Args:
        df: The parsed DataFrame to validate.
        
    Returns:
        True if validation passes, False otherwise.
        
    Raises:
        ValueError: If validation fails, with details in the error message.
    """
    logger.info("Starting input schema validation...")
    is_valid, errors = validate_input_schema(df)
    
    if not is_valid:
        error_msg = f"Input schema validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("Input schema validation passed.")
    return True