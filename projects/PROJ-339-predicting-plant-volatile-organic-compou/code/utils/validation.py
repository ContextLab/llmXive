"""
Validation utilities for data integrity.
Implements T006.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Set
from pathlib import Path
import json

def check_replicates(df: pd.DataFrame, group_col: str, min_count: int = 3) -> Tuple[bool, List[str]]:
    """
    Check if all groups have at least min_count replicates.
    """
    counts = df.groupby(group_col).size()
    low_replicates = counts[counts < min_count].index.tolist()
    return len(low_replicates) == 0, low_replicates

def validate_data_types(df: pd.DataFrame) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that numeric columns contain only numeric values.
    """
    errors = []
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if not pd.api.types.is_numeric_dtype(df[col]):
            errors.append(f"Column {col} is not numeric.")
    
    # Check for non-numeric in columns that should be numeric but are object
    object_cols = df.select_dtypes(include=['object']).columns
    for col in object_cols:
        # Try to convert
        try:
            pd.to_numeric(df[col], errors='raise')
        except ValueError:
            errors.append(f"Column {col} contains non-numeric values.")

    return len(errors) == 0, {"valid": len(errors) == 0, "errors": errors}

def validate_environmental_metadata(df: pd.DataFrame, required_cols: List[str]) -> Tuple[bool, List[str]]:
    """
    Check for missing values in critical environmental columns.
    """
    missing = []
    for col in required_cols:
        if col not in df.columns:
            missing.append(f"Missing column: {col}")
        elif df[col].isnull().sum() > 0:
            missing.append(f"Column {col} has {df[col].isnull().sum()} nulls")
    return len(missing) == 0, missing

def generate_validation_report(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate a comprehensive validation report.
    """
    is_valid, errors = validate_data_types(df)
    return {
        "valid": is_valid,
        "row_count": len(df),
        "column_count": len(df.columns),
        "errors": errors
    }
