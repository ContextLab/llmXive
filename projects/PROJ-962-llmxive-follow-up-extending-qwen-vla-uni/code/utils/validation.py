"""
validation.py - Data validation schema and checksumming logic.
"""
import hashlib
import json
import os
from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd
import numpy as np

def compute_file_checksum(filepath: str, algorithm: str = 'sha256') -> str:
    """Compute the checksum of a file."""
    hash_func = hashlib.new(algorithm)
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def validate_dataframe_schema(df: pd.DataFrame, expected_schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that a DataFrame matches an expected schema.
    expected_schema: Dict mapping column names to expected dtypes.
    Returns: (is_valid, list_of_errors)
    """
    errors = []
    for col, dtype in expected_schema.items():
        if col not in df.columns:
            errors.append(f"Missing column: {col}")
        elif str(df[col].dtype) != str(dtype):
            errors.append(f"Column '{col}' has dtype {df[col].dtype}, expected {dtype}")
    return len(errors) == 0, errors

def validate_numeric_bounds(df: pd.DataFrame, column: str, min_val: float, max_val: float) -> Tuple[bool, List[str]]:
    """
    Validate that a column's values are within [min_val, max_val].
    """
    errors = []
    if column not in df.columns:
        return False, [f"Column '{column}' not found"]
    
    col_data = df[column].dropna()
    if col_data.min() < min_val or col_data.max() > max_val:
        errors.append(f"Column '{column}' out of bounds [{min_val}, {max_val}]")
    
    return len(errors) == 0, errors

def validate_cluster_assignments(assignments: pd.DataFrame, cluster_ids: List[int]) -> Tuple[bool, List[str]]:
    """
    Validate that all assignments belong to valid cluster IDs.
    """
    errors = []
    if 'cluster_id' not in assignments.columns:
        return False, ["Missing 'cluster_id' column"]
    
    invalid_ids = set(assignments['cluster_id'].unique()) - set(cluster_ids)
    if invalid_ids:
        errors.append(f"Invalid cluster IDs found: {invalid_ids}")
    
    return len(errors) == 0, errors

def validate_trajectory_consistency(trajectory: np.ndarray, expected_dim: int) -> Tuple[bool, List[str]]:
    """
    Validate that a trajectory has the expected dimensionality.
    """
    errors = []
    if trajectory.shape[1] != expected_dim:
        errors.append(f"Trajectory dimension {trajectory.shape[1]} != expected {expected_dim}")
    return len(errors) == 0, errors

def generate_validation_report(results: Dict[str, Tuple[bool, List[str]]]) -> str:
    """
    Generate a human-readable validation report from a dict of results.
    """
    lines = ["Validation Report"]
    for name, (is_valid, errors) in results.items():
        status = "PASS" if is_valid else "FAIL"
        lines.append(f"{name}: {status}")
        if not is_valid:
            for err in errors:
                lines.append(f"  - {err}")
    return "\n".join(lines)
