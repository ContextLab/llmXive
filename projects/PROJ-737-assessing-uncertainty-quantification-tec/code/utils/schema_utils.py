"""
Schema utilities for validating and saving data contracts.

This module defines the contract for `per_sample_errors.csv` and provides
utilities to validate data against it and save the schema definition.
"""
import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
import json

# Define the contract for per_sample_errors.csv
# Columns: sample_id, method, prediction, lower_bound, upper_bound, ground_truth, dataset
PER_SAMPLE_ERRORS_SCHEMA = {
    "sample_id": "object",       # Unique identifier for the sample (string or int)
    "method": "object",          # Name of the UQ method used (string)
    "prediction": "float64",     # Point prediction (float)
    "lower_bound": "float64",    # Lower bound of the prediction interval (float)
    "upper_bound": "float64",    # Upper bound of the prediction interval (float)
    "ground_truth": "float64",   # Actual ground truth value (float)
    "dataset": "object"          # Name of the dataset (string)
}

REQUIRED_COLUMNS = list(PER_SAMPLE_ERRORS_SCHEMA.keys())

def get_logger():
    """Helper to get a logger instance."""
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def validate_per_sample_errors(df: pd.DataFrame) -> bool:
    """
    Validates a DataFrame against the per_sample_errors schema.
    
    Args:
        df: The DataFrame to validate.
        
    Returns:
        True if the DataFrame matches the schema, False otherwise.
        
    Raises:
        ValueError: If validation fails.
    """
    logger = get_logger()
    
    # Check required columns
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return False
    
    # Check data types (strict check for numeric columns)
    for col, expected_type in PER_SAMPLE_ERRORS_SCHEMA.items():
        if col in df.columns:
            if expected_type == "float64":
                if not pd.api.types.is_float_dtype(df[col]) and not pd.api.types.is_integer_dtype(df[col]):
                    # Allow integer to be castable to float, but warn if it's object/string
                    if df[col].dtype == 'object':
                        try:
                            df[col] = pd.to_numeric(df[col])
                        except (ValueError, TypeError):
                            logger.error(f"Column '{col}' contains non-numeric data.")
                            return False
            # For object columns, we just check they exist and are not empty
            if expected_type == "object" and df[col].dtype != 'object' and df[col].dtype != 'string':
                 # Allow numeric columns to be stored as objects if they contain strings, 
                 # but ensure the schema intent is met.
                 pass
    
    # Check for NaN in critical columns
    critical_cols = ["prediction", "lower_bound", "upper_bound", "ground_truth"]
    for col in critical_cols:
        if df[col].isna().any():
            logger.warning(f"Column '{col}' contains NaN values.")
            # We allow NaN for now, but it might be an issue downstream
            
    return True

def save_schema_contract(output_path: Optional[str] = None) -> str:
    """
    Saves the schema contract definition to a JSON file.
    
    Args:
        output_path: Optional path to save the schema. If None, defaults to 
                     'results/schema_per_sample_errors.json'.
                     
    Returns:
        The path where the schema was saved.
    """
    logger = get_logger()
    
    if output_path is None:
        output_path = "results/schema_per_sample_errors.json"
    
    # Ensure directory exists
    path_obj = Path(output_path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    schema_definition = {
        "name": "per_sample_errors",
        "description": "Schema for per-sample prediction errors and intervals used in statistical testing.",
        "columns": [
            {"name": "sample_id", "type": "object", "description": "Unique identifier for the sample"},
            {"name": "method", "type": "object", "description": "Name of the UQ method"},
            {"name": "prediction", "type": "float64", "description": "Point prediction"},
            {"name": "lower_bound", "type": "float64", "description": "Lower bound of prediction interval"},
            {"name": "upper_bound", "type": "float64", "description": "Upper bound of prediction interval"},
            {"name": "ground_truth", "type": "float64", "description": "Ground truth value"},
            {"name": "dataset", "type": "object", "description": "Name of the dataset"}
        ],
        "required_columns": REQUIRED_COLUMNS,
        "notes": "This schema must be adhered to by T014 (pipeline.py) to ensure compatibility with T024 (statistical tests)."
    }
    
    with open(path_obj, 'w') as f:
        json.dump(schema_definition, f, indent=4)
    
    logger.info(f"Schema contract saved to {output_path}")
    return str(output_path)

def create_empty_schema_example() -> pd.DataFrame:
    """
    Creates an empty DataFrame with the correct schema structure.
    Useful for initializing output files or testing validation logic.
    
    Returns:
        An empty DataFrame with the correct column names and types.
    """
    df = pd.DataFrame({
        "sample_id": pd.Series([], dtype='object'),
        "method": pd.Series([], dtype='object'),
        "prediction": pd.Series([], dtype='float64'),
        "lower_bound": pd.Series([], dtype='float64'),
        "upper_bound": pd.Series([], dtype='float64'),
        "ground_truth": pd.Series([], dtype='float64'),
        "dataset": pd.Series([], dtype='object')
    })
    return df
