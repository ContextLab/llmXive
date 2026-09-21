"""
Data Validation Module.

This module provides functionality to validate datasets against schema contracts.
It ensures that input and output DataFrames conform to the expected structure
defined in the `contracts/` directory.

Functions:
    load_schema: Loads a YAML schema definition.
    validate_dataframe_against_schema: Checks a DataFrame against a schema.
    validate_input_schema: Validates the raw input data structure.
    validate_output_schema: Validates the processed output data structure.
    validate_parsed_data: Orchestrates validation of parsed data.
"""
import logging
import json
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import yaml
import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """
    Loads a schema definition from a YAML file.

    Args:
        schema_path: Path to the schema YAML file.

    Returns:
        Dictionary representing the schema.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the file is not valid YAML.
    """
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_dataframe_against_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates a DataFrame against a schema definition.

    Args:
        df: The DataFrame to validate.
        schema: The schema dictionary.

    Returns:
        A tuple (is_valid, list_of_errors).
    """
    errors = []
    required_columns = schema.get('required_columns', [])
    
    for col in required_columns:
        if col not in df.columns:
            errors.append(f"Missing required column: {col}")
    
    # Add type checking logic here if schema defines types
    return len(errors) == 0, errors

def validate_input_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validates the input data against the dataset schema.

    Args:
        df: The input DataFrame.

    Returns:
        A tuple (is_valid, list_of_errors).
    """
    schema_path = Path("contracts/dataset.schema.yaml")
    if not schema_path.exists():
        logger.warning("Input schema file not found. Skipping validation.")
        return True, []
    
    schema = load_schema(schema_path)
    return validate_dataframe_against_schema(df, schema)

def validate_output_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validates the output data against the output schema.

    Args:
        df: The output DataFrame.

    Returns:
        A tuple (is_valid, list_of_errors).
    """
    schema_path = Path("contracts/output.schema.yaml")
    if not schema_path.exists():
        logger.warning("Output schema file not found. Skipping validation.")
        return True, []
    
    schema = load_schema(schema_path)
    return validate_dataframe_against_schema(df, schema)

def validate_parsed_data(df: pd.DataFrame) -> bool:
    """
    Orchestrates validation of parsed data.

    Args:
        df: The parsed DataFrame.

    Returns:
        True if valid, False otherwise.
    """
    is_valid, errors = validate_input_schema(df)
    if not is_valid:
        for err in errors:
            logger.error(f"Validation error: {err}")
        return False
    return True

def main():
    """
    Entry point for testing the validator module directly.
    """
    logger.info("Validator module initialized.")
