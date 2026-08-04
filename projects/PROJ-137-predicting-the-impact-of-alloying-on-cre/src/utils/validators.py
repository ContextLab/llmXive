"""
Schema validation and physics consistency checks.
"""
import pandas as pd
import yaml
import os
from typing import List, Dict, Any

def validate_schema(df: pd.DataFrame, schema_path: str) -> bool:
    """
    Validate DataFrame against a YAML schema.
    
    Args:
        df: DataFrame to validate.
        schema_path: Path to schema YAML file.
        
    Returns:
        True if valid, False otherwise.
    """
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
        
    required_cols = schema.get('required_columns', [])
    type_map = schema.get('column_types', {})
    
    # Check columns
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
        
    # Check types (basic)
    for col, dtype in type_map.items():
        if col in df.columns:
            if dtype == 'numeric' and not pd.api.types.is_numeric_dtype(df[col]):
                raise TypeError(f"Column {col} must be numeric")
            elif dtype == 'string' and not pd.api.types.is_string_dtype(df[col]):
                raise TypeError(f"Column {col} must be string")
                
    return True
