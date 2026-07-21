"""
Schema definitions and validation logic for project datasets.
"""
import pandas as pd
from typing import Dict, List, Any, Optional
import json
from pathlib import Path

# Load schema from the contract file
_SCHEMA_PATH = Path(__file__).parent.parent.parent / "contracts" / "data_schema.json"

def _load_schema() -> Dict[str, Any]:
    """Load the JSON schema definition."""
    if not _SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found at {_SCHEMA_PATH}")
    with open(_SCHEMA_PATH, "r") as f:
        return json.load(f)

def get_schema(dataset_name: str) -> Dict[str, Any]:
    """
    Retrieve the schema definition for a specific dataset.
    
    Args:
        dataset_name: The key name of the dataset (e.g., 'target_list', 'repo_metrics').
        
    Returns:
        Dictionary containing the schema definition.
        
    Raises:
        KeyError: If the dataset name is not found in the schema.
    """
    schema = _load_schema()
    if dataset_name not in schema["datasets"]:
        raise KeyError(f"Dataset '{dataset_name}' not found in schema. Available: {list(schema['datasets'].keys())}")
    return schema["datasets"][dataset_name]

def validate_dataframe(df: pd.DataFrame, dataset_name: str) -> List[str]:
    """
    Validate a DataFrame against a named schema.
    
    Args:
        df: The DataFrame to validate.
        dataset_name: The key name of the dataset schema to use.
        
    Returns:
        A list of validation error messages. Empty if valid.
    """
    errors = []
    try:
        schema = get_schema(dataset_name)
    except KeyError as e:
        return [str(e)]

    required_cols = schema["columns"].keys()
    actual_cols = set(df.columns)
    missing_cols = set(required_cols) - actual_cols
    
    if missing_cols:
        errors.append(f"Missing columns: {missing_cols}")
    
    extra_cols = actual_cols - set(required_cols)
    if extra_cols:
        errors.append(f"Unexpected columns: {extra_cols}")

    for col_name, col_def in schema["columns"].items():
        if col_name not in df.columns:
            continue
        
        # Check nullability
        if col_def.get("nullable") is False:
            if df[col_name].isna().any():
                errors.append(f"Column '{col_name}' contains null values but is marked as non-nullable.")
        
        # Check uniqueness
        if col_def.get("unique") is True:
            if df[col_name].duplicated().any():
                errors.append(f"Column '{col_name}' contains duplicate values but is marked as unique.")
        
        # Basic type check (pandas often infers mixed types, so we check for object vs expected)
        expected_type = col_def.get("type")
        if expected_type == "integer":
            if not pd.api.types.is_integer_dtype(df[col_name]):
                # Allow float if it has no decimals, but warn if it's object
                if not (pd.api.types.is_float_dtype(df[col_name]) and (df[col_name] % 1 == 0).all()):
                    errors.append(f"Column '{col_name}' expected integer, got {df[col_name].dtype}")
        elif expected_type == "float":
            if not (pd.api.types.is_float_dtype(df[col_name]) or pd.api.types.is_integer_dtype(df[col_name])):
                errors.append(f"Column '{col_name}' expected float, got {df[col_name].dtype}")
        elif expected_type == "string":
            if not pd.api.types.is_string_dtype(df[col_name]) and not pd.api.types.is_object_dtype(df[col_name]):
                errors.append(f"Column '{col_name}' expected string, got {df[col_name].dtype}")

    return errors
