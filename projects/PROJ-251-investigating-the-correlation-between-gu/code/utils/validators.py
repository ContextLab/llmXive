import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from pathlib import Path
import json
import jsonschema
from jsonschema import validate, ValidationError

def validate_dataset_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate the dataset dictionary against the provided JSON schema.
    
    Args:
        data: The dataset dictionary to validate
        schema: The JSON schema to validate against
    
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        # Convert schema to JSON-compatible format if needed
        # The schema loaded from YAML should already be a dict
        validate(instance=data, schema=schema)
        return True
    except ValidationError as e:
        print(f"Schema validation error: {e.message}")
        return False

def validate_correlation_results_schema(results: pd.DataFrame) -> bool:
    """
    Validate correlation results DataFrame.
    
    Expected columns:
    - taxa: string
    - coefficient: float
    - p_value: float
    - adj_p_value: float
    """
    required_cols = ['taxa', 'coefficient', 'p_value', 'adj_p_value']
    
    if not all(col in results.columns for col in required_cols):
        missing = [c for c in required_cols if c not in results.columns]
        raise ValueError(f"Missing required columns: {missing}")
    
    # Check for nulls in critical columns
    for col in ['coefficient', 'p_value', 'adj_p_value']:
        if results[col].isnull().any():
            raise ValueError(f"Column {col} contains null values")
    
    return True

def validate_model_metrics_schema(metrics: Dict[str, Any]) -> bool:
    """
    Validate model metrics dictionary.
    
    Expected keys:
    - accuracy: float
    - precision: float
    - recall: float
    - f1_score: float
    - confusion_matrix: list
    """
    required_keys = ['accuracy', 'precision', 'recall', 'f1_score', 'confusion_matrix']
    
    if not all(key in metrics for key in required_keys):
        missing = [k for k in required_keys if k not in metrics]
        raise ValueError(f"Missing required keys: {missing}")
    
    # Validate numeric types
    for key in ['accuracy', 'precision', 'recall', 'f1_score']:
        if not isinstance(metrics[key], (int, float)):
            raise ValueError(f"Key {key} must be numeric")
        if not 0 <= metrics[key] <= 1:
            raise ValueError(f"Key {key} must be between 0 and 1")
    
    # Validate confusion matrix
    if not isinstance(metrics['confusion_matrix'], list) or len(metrics['confusion_matrix']) != 2:
        raise ValueError("confusion_matrix must be a list of 2 lists")
    
    return True

def validate_file_exists(file_path: Path) -> bool:
    """Check if a file exists."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    return True

def validate_dataframe_not_empty(df: pd.DataFrame) -> bool:
    """Check if a DataFrame is not empty."""
    if df.empty:
        raise ValueError("DataFrame is empty")
    return True