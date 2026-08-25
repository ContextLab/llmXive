"""
Validation utilities for data integrity.
Implements T006: Replicate checks and data type validation.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Set
from pathlib import Path
import json


def check_replicates(df: pd.DataFrame, group_col: str, min_count: int = 3) -> Tuple[bool, List[str]]:
    """
    Check if all groups in the specified column have at least min_count replicates.
    
    Args:
        df: Input DataFrame.
        group_col: Column name to group by (e.g., 'experimental_condition').
        min_count: Minimum required count per group.
    
    Returns:
        Tuple of (all_valid, list_of_failing_groups).
        all_valid is True if all groups meet the threshold.
    """
    if group_col not in df.columns:
        raise ValueError(f"Group column '{group_col}' not found in DataFrame.")
    
    counts = df.groupby(group_col).size()
    # Identify groups with counts strictly less than min_count
    low_replicates = counts[counts < min_count].index.tolist()
    all_valid = len(low_replicates) == 0
    
    return all_valid, low_replicates


def validate_data_types(df: pd.DataFrame) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that columns expected to be numeric are indeed numeric or convertible.
    Checks for non-numeric values in object columns that should be numeric.
    
    Args:
        df: Input DataFrame.
    
    Returns:
        Tuple of (is_valid, details_dict).
        details_dict contains 'valid' boolean and a list of error messages.
    """
    errors: List[str] = []
    
    # Check explicitly numeric columns for non-numeric dtypes (should be rare but possible)
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if not pd.api.types.is_numeric_dtype(df[col]):
            errors.append(f"Column '{col}' is declared numeric but has dtype {df[col].dtype}.")
    
    # Check object columns for non-numeric content
    object_cols = df.select_dtypes(include=['object', 'string']).columns
    for col in object_cols:
        # Skip if column is clearly non-numeric (e.g., IDs, names) based on sample?
        # For strict validation, we try to parse. If it fails, it's an error if we expect numeric.
        # We assume any object column might need to be numeric for downstream ML.
        try:
            pd.to_numeric(df[col], errors='raise')
        except (ValueError, TypeError):
            errors.append(f"Column '{col}' (object dtype) contains non-numeric values.")
    
    is_valid = len(errors) == 0
    return is_valid, {"valid": is_valid, "errors": errors}


def validate_environmental_metadata(df: pd.DataFrame, required_cols: List[str]) -> Tuple[bool, List[str]]:
    """
    Check for missing values in critical environmental columns.
    
    Args:
        df: Input DataFrame.
        required_cols: List of column names that must be present and non-null.
    
    Returns:
        Tuple of (all_valid, list_of_issues).
    """
    issues: List[str] = []
    for col in required_cols:
        if col not in df.columns:
            issues.append(f"Missing required column: '{col}'")
        else:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                issues.append(f"Column '{col}' has {null_count} null/missing values.")
    
    return len(issues) == 0, issues


def generate_validation_report(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate a comprehensive validation report for a DataFrame.
    
    Args:
        df: Input DataFrame.
    
    Returns:
        Dictionary containing validation summary.
    """
    is_valid, details = validate_data_types(df)
    
    report = {
        "valid": is_valid,
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": list(df.columns),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "errors": details.get("errors", [])
    }
    
    return report
