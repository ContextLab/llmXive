"""
Utility functions for loading and validating dataset schemas.
"""
import os
import yaml
import pandas as pd
from typing import Dict, Any

def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load a YAML schema definition file.
    
    Args:
        schema_path: Path to the .yaml schema file.
        
    Returns:
        Dictionary containing the schema definition.
    """
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_dataframe(df: pd.DataFrame, schema: Dict[str, Any], dataset_name: str) -> bool:
    """
    Validate a DataFrame against a specific dataset schema.
    
    Args:
        df: The DataFrame to validate.
        schema: The full schema dictionary.
        dataset_name: The key in the schema corresponding to this dataset (e.g., 'noise_mapped').
        
    Returns:
        True if valid, raises AssertionError if invalid.
    """
    if dataset_name not in schema:
        raise ValueError(f"Schema definition for '{dataset_name}' not found.")
    
    expected_cols = set(schema[dataset_name]['columns'].keys())
    actual_cols = set(df.columns)
    
    missing = expected_cols - actual_cols
    extra = actual_cols - expected_cols
    
    if missing:
        raise AssertionError(f"Missing columns: {missing}")
    if extra:
        raise AssertionError(f"Extra columns: {extra}")
        
    # Type and constraint checks could be added here
    return True
