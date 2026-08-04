import hashlib
import json
import os
from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd
import numpy as np

def compute_file_checksum(file_path: str, algorithm: str = 'sha256') -> str:
    """
    Compute the checksum of a file.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use.
        
    Returns:
        Hexadecimal checksum string.
    """
    hasher = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hasher.update(chunk)
    return hasher.hexdigest()

def validate_dataframe_schema(
    df: pd.DataFrame, 
    expected_columns: List[str],
    expected_dtypes: Optional[Dict[str, str]] = None
) -> Tuple[bool, List[str]]:
    """
    Validate that a DataFrame has the expected columns and optional dtypes.
    
    Args:
        df: DataFrame to validate.
        expected_columns: List of expected column names.
        expected_dtypes: Optional dictionary mapping column names to expected dtypes.
        
    Returns:
        Tuple of (is_valid, list of error messages).
    """
    errors = []
    
    missing_cols = set(expected_columns) - set(df.columns)
    if missing_cols:
        errors.append(f"Missing columns: {missing_cols}")
        
    if expected_dtypes:
        for col, expected_dtype in expected_dtypes.items():
            if col in df.columns:
                actual_dtype = str(df[col].dtype)
                if expected_dtype not in actual_dtype:
                    errors.append(f"Column '{col}' has dtype {actual_dtype}, expected {expected_dtype}")
                    
    return len(errors) == 0, errors

def validate_numeric_bounds(
    data: Union[np.ndarray, pd.Series, List[float]],
    lower_bound: Optional[float] = None,
    upper_bound: Optional[float] = None
) -> Tuple[bool, List[str]]:
    """
    Validate that numeric data falls within specified bounds.
    
    Args:
        data: Numeric data to validate.
        lower_bound: Optional lower bound.
        upper_bound: Optional upper bound.
        
    Returns:
        Tuple of (is_valid, list of error messages).
    """
    data = np.asarray(data)
    errors = []
    
    if lower_bound is not None:
        violations = data < lower_bound
        if np.any(violations):
            count = np.sum(violations)
            errors.append(f"{count} values below lower bound {lower_bound}")
            
    if upper_bound is not None:
        violations = data > upper_bound
        if np.any(violations):
            count = np.sum(violations)
            errors.append(f"{count} values above upper bound {upper_bound}")
            
    return len(errors) == 0, errors

def validate_cluster_assignments(
    assignments: np.ndarray,
    n_clusters: int,
    min_cluster_size: int = 100
) -> Tuple[bool, List[str]]:
    """
    Validate cluster assignments.
    
    Args:
        assignments: Array of cluster labels.
        n_clusters: Expected number of clusters.
        min_cluster_size: Minimum samples per cluster.
        
    Returns:
        Tuple of (is_valid, list of error messages).
    """
    errors = []
    unique_labels = np.unique(assignments)
    
    if len(unique_labels) != n_clusters:
        errors.append(f"Expected {n_clusters} clusters, found {len(unique_labels)}")
        
    for label in unique_labels:
        count = np.sum(assignments == label)
        if count < min_cluster_size:
            errors.append(f"Cluster {label} has only {count} samples (min: {min_cluster_size})")
            
    return len(errors) == 0, errors

def validate_trajectory_consistency(
    trajectory: np.ndarray,
    expected_dims: int,
    min_length: int = 10
) -> Tuple[bool, List[str]]:
    """
    Validate trajectory consistency.
    
    Args:
        trajectory: Array of shape (T, D).
        expected_dims: Expected number of dimensions.
        min_length: Minimum number of time steps.
        
    Returns:
        Tuple of (is_valid, list of error messages).
    """
    errors = []
    trajectory = np.asarray(trajectory)
    
    if trajectory.ndim != 2:
        errors.append(f"Trajectory must be 2D, got {trajectory.ndim}D")
    else:
        if trajectory.shape[1] != expected_dims:
            errors.append(f"Expected {expected_dims} dimensions, got {trajectory.shape[1]}")
        if trajectory.shape[0] < min_length:
            errors.append(f"Trajectory length {trajectory.shape[0]} < minimum {min_length}")
            
    return len(errors) == 0, errors

def generate_validation_report(
    results: Dict[str, Tuple[bool, List[str]]]
) -> str:
    """
    Generate a human-readable validation report.
    
    Args:
        results: Dictionary mapping test names to (is_valid, errors) tuples.
        
    Returns:
        Formatted report string.
    """
    lines = []
    lines.append("Validation Report")
    lines.append("=" * 40)
    
    all_passed = True
    for name, (is_valid, errors) in results.items():
        status = "PASSED" if is_valid else "FAILED"
        lines.append(f"\n{name}: {status}")
        if not is_valid:
            all_passed = False
            for error in errors:
                lines.append(f"  - {error}")
                
    lines.append("\n" + "=" * 40)
    lines.append(f"Overall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    
    return "\n".join(lines)
